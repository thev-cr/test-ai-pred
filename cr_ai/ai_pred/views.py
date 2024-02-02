import json
from django.http import JsonResponse
import os
import pymongo
import pandas as pd
import certifi
from joblib import load
from django.views.decorators.csrf import csrf_exempt


# MongoDB Connection
def connect():
    mongo_uri = os.environ.get('MONGO_URI')
    client = pymongo.MongoClient(mongo_uri, tlsCAFile=certifi.where())
    db = client.imaginary
    client.admin.command('ping')
    print('Connected to db')
    universities_col = db['universities']
    courses_col = db['courses']
    universities = list(universities_col.find({}))
    courses = list(courses_col.find({}))
    return universities, courses


# Function to predict university rating
def predict_uni_rating(ug_gpa, gre):
    pipeline = load('knn_regressor_model.joblib')
    input_data = pd.DataFrame({'ug_gpa': [ug_gpa], 'gre': [gre], 'status': 'Accepted'})  # status is dummy
    predicted_rating = pipeline.predict(input_data)[0]
    return predicted_rating


# Function to categorize university
def categorize_university(uni_rating, predicted_rating):
    if predicted_rating - 1 <= uni_rating < predicted_rating - 0.35:
        return 'Safe'
    elif predicted_rating - 0.35 <= uni_rating <= predicted_rating + 0.25:
        return 'Moderate'
    elif predicted_rating + 0.25 < uni_rating <= predicted_rating + 1:
        return 'Ambitious'
    return 'Outside Range'


@csrf_exempt
def predict(request):
    try:
        body = json.loads(request.body)
        ug_gpa = body['ug_gpa']
        gre = body['gre']
        chosen_sub_discipline = body['sub_discipline']

        universities, courses = connect()
        predicted_rating = predict_uni_rating(ug_gpa, gre)

        # Filter and categorize universities
        matching_universities = {}
        for uni in universities:
            uni_rating = uni.get('uni_rating')
            if uni_rating is None:
                continue
            category = categorize_university(uni_rating, predicted_rating)
            if category != 'Outside Range':
                matching_universities[str(uni['_id'])] = {'name': uni['name'], 'category': category}

        # Filter courses based on matching universities and user's sub-discipline preference
        matching_courses = []
        for course in courses:
            if str(course['university']) in matching_universities and chosen_sub_discipline in course['subDiscipline']:
                matching_courses.append({
                    "Course": course['name'],
                    "University": matching_universities[str(course['university'])]['name'],
                    "Category": matching_universities[str(course['university'])]['category'],
                    "CID": str(course['_id'])
                })

        return JsonResponse(matching_courses, safe=False)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
