import os
import requests
import json
import csv
import time
import traceback

# base dir
base_dir = os.path.dirname(os.path.abspath(__file__))

# review shake api token
spiderman_token = "aeb256bfba92a5bdf5d2fb6c3866d25759ccb52c"

# review shake api header
headers = {
    'spiderman-token': spiderman_token,
    }

# result output file name
result_csv_name = "result-{}.csv".format(time.strftime("%Y-%m-%d-%H-%M-%S"))
result_csv_path = base_dir + "/output/" + result_csv_name

# the path of yelp_business_urls.csv
yelp_business_urls_csv_path = "{base_dir}/resources/{file_name}".format(base_dir=base_dir, file_name="yelp_business_urls.csv")

# the path of google_business_queries.csv
google_business_queries_csv_path = "{base_dir}/resources/{file_name}".format(base_dir=base_dir, file_name="google_business_queries.csv")

# get all request urls
def get_url_list():
    # total review request urls list
    review_request_urls_list = list()
    
    try:
        # check yelp_business_urls.csv exist
        if os.path.isfile(yelp_business_urls_csv_path):
            with open(yelp_business_urls_csv_path, 'r') as yelp_csv:
                reader = csv.reader(yelp_csv)

                for value in reader:
                    if value:
                        review_request_urls_list.append(['Yelp', value[0]])
        
        # check google_business_queries.csv exist
        if os.path.isfile(google_business_queries_csv_path):
            with open(google_business_queries_csv_path, 'r') as google_csv:
                reader = csv.reader(google_csv)

                for value in reader:
                    if value:
                        review_request_urls_list.append(['Google', value[0]])
        
    except:
        print(traceback.print_exc())
    
    return review_request_urls_list

# make query string             
def make_querystring(arg):
    try:
        # if review site is Yelp
        if arg[0] == 'Yelp':
            query_string = {"url" : arg[1].strip()}
        elif arg[0] == 'Google':
            query_string = {"query" : arg[1].strip()}
        else:
            query_string = {}
        
        return query_string
    except:
        print(traceback.print_exc())

# add business url or google query to review shake api
def add_reviews(review_request_urls):
    job_id_list = list()

    for review_request_url in review_request_urls:
        try:
            url = "https://app.datashake.com/api/v2/profiles/add"
            # make querystring
            querystring = make_querystring(review_request_url)
            
            if querystring:
                response = requests.request("POST", url, headers=headers, params=querystring)
                response_dict = json.loads(response.text)

                job_id = None
                if "success" in response_dict and response_dict["success"]:
                    job_id = response_dict["job_id"]
                    job_id_list.append(job_id)
        except:
            print(traceback.print_exc())

    return job_id_list

# get status of added profile
def get_status(job_id):
    url = "https://app.datashake.com/api/v2/profiles/jobs/{}".format(str(job_id))
    querystring = {}
    payload = ""
    response = requests.request("GET", url, data=payload, headers=headers, params=querystring)
    response_dict = json.loads(response.text)
    
    return response_dict["status"]

# get reviews from added profile
def get_reviews_store(job_id):
    global result_csv_path

    url = "https://app.datashake.com/api/v2/profiles/reviews"
    querystring = {"job_id" : job_id, "per_page" : 100, "allow_response" : True}
    response = requests.request("GET", url, headers=headers, params=querystring)
    response_dict = json.loads(response.text)
    
    if len(response_dict["reviews"]):
        for index in range(len(response_dict["reviews"])):
            
            # csv row
            row_dict = dict()
            row_dict["job id"] = response_dict["job_id"]
            row_dict["meta data-name"] = json.loads(response_dict["meta_data"])["name"]
            row_dict["review id"] = response_dict["reviews"][index]["id"]
            row_dict["name"] = response_dict["reviews"][index]["name"]
            row_dict["date"] = response_dict["reviews"][index]["date"]
            row_dict["rating_value"] = response_dict["reviews"][index]["rating_value"]
            row_dict["review_title"] = response_dict["reviews"][index]["review_title"]
            row_dict["review_text"] = response_dict["reviews"][index]["review_text"]
            row_dict["url"] = response_dict["reviews"][index]["url"]
            row_dict["language_code"] = response_dict["reviews"][index]["language_code"]
            row_dict["unique_id"] = response_dict["reviews"][index]["unique_id"]
            row_dict["location"] = response_dict["reviews"][index]["location"]
            row_dict["source"] = response_dict["source_url"]
            
            # check result file exist
            file_exist = os.path.isfile(result_csv_path)
            with open (result_csv_path, 'a', newline="", encoding="utf-8") as result_csv_file:
                fieldnames = ["job id", "meta data-name", "review id", "name", "date", "rating_value", "review_title", "review_text", "url", "language_code", "unique_id", "location", "source"]
                writer = csv.DictWriter(result_csv_file, fieldnames=fieldnames)
                if not file_exist:
                    writer.writeheader()
                writer.writerow(row_dict)

def main():
    # read all business urls
    review_request_urls_list = get_url_list()

    if review_request_urls_list:
        # add review profile
        job_id_list = add_reviews(review_request_urls_list)
        
        while bool(job_id_list):
            for job_id in job_id_list:
                # check request status
                status_value = get_status(job_id)
                print('-----------------------------------')
                if status_value == "complete":
                    print("Job id {} was completed successfully.".format(job_id))
                    # get reviews from added profile and store as csv file
                    get_reviews_store(job_id)
                    job_id_list.remove(job_id)
                elif status_value == "pending":
                    print("Job id {} is in pending status.".format(job_id))
                    pass
                elif status_value == "maintenance" or status_value == "failed":
                    print("You can't get response. Please try again later.")
                    job_id_list.remove(job_id)
                else:
                    print("--- Invalid URL. Please check your request URL. ---")
                    job_id_list.remove(job_id)

            time.sleep(10)
    else:
        print("Please check your business URL external file.")

if __name__ == '__main__':
    main()