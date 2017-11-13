## import statements
import requests_oauthlib
import webbrowser
import json
from secret_data import *
from datetime import datetime

## CACHING SETUP
#--------------------------------------------------
# Caching constants
#--------------------------------------------------

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
DEBUG = False
CACHE_FNAME = "cache_contents.json"
CREDS_CACHE_FILE = "creds.json"

#--------------------------------------------------
# Load cache files: data and credentials
#--------------------------------------------------
# Load data cache
try:
    with open(CACHE_FNAME, 'r') as cache_file:
        cache_json = cache_file.read()
        CACHE_DICTION = json.loads(cache_json)
except:
    CACHE_DICTION = {}

# Load creds cache
try:
    with open(CREDS_CACHE_FILE,'r') as creds_file:
        cache_creds = creds_file.read()
        CREDS_DICTION = json.loads(cache_creds)
except:
    CREDS_DICTION = {}

#---------------------------------------------
# Cache functions
#---------------------------------------------
def has_cache_expired(timestamp_str, expire_in_days):
    """Check if cache timestamp is over expire_in_days old"""
    # gives current datetime
    now = datetime.now()

    # datetime.strptime converts a formatted string into datetime object
    cache_timestamp = datetime.strptime(timestamp_str, DATETIME_FORMAT)

    # subtracting two datetime objects gives you a timedelta object
    delta = now - cache_timestamp
    delta_in_days = delta.days


    # now that we have days as integers, we can just use comparison
    # and decide if cache has expired or not
    if delta_in_days > expire_in_days:
        return True # It's been longer than expiry time
    else:
        return False

def get_from_cache(identifier, dictionary):
    """If unique identifier exists in specified cache dictionary and has not expired, return the data associated with it from the request, else return None"""
    identifier = identifier.upper() # Assuming none will differ with case sensitivity here
    if identifier in dictionary:
        data_assoc_dict = dictionary[identifier]
        if has_cache_expired(data_assoc_dict['timestamp'],data_assoc_dict["expire_in_days"]):
            if DEBUG:
                print("Cache has expired for {}".format(identifier))
            # also remove old copy from cache
            del dictionary[identifier]
            data = None
        else:
            data = dictionary[identifier]['values']
    else:
        data = None
    return data


def set_in_data_cache(identifier, data, expire_in_days):
    """Add identifier and its associated values (literal data) to the data cache dictionary, and save the whole dictionary to a file as json"""
    identifier = identifier.upper()
    CACHE_DICTION[identifier] = {
        'values': data,
        'timestamp': datetime.now().strftime(DATETIME_FORMAT),
        'expire_in_days': expire_in_days
    }

    with open(CACHE_FNAME, 'w') as cache_file:
        cache_json = json.dumps(CACHE_DICTION)
        cache_file.write(cache_json)

def set_in_creds_cache(identifier, data, expire_in_days):
    """Add identifier and its associated values (literal data) to the credentials cache dictionary, and save the whole dictionary to a file as json"""
    identifier = identifier.upper() # make unique
    CREDS_DICTION[identifier] = {
        'values': data,
        'timestamp': datetime.now().strftime(DATETIME_FORMAT),
        'expire_in_days': expire_in_days
    }

    with open(CREDS_CACHE_FILE, 'w') as cache_file:
        cache_json = json.dumps(CREDS_DICTION)
        cache_file.write(cache_json)

#####
## ADDITIONAL CODE for program should go here...
## Perhaps authentication setup, functions to get and process data, a class definition... etc.

## OAuth1 API Constants - vary by API
### Private data in a hidden secret_data.py file
CLIENT_KEY = client_key # what Twitter calls Consumer Key
CLIENT_SECRET = client_secret # What Twitter calls Consumer Secret

### Specific to API URLs, not private
REQUEST_TOKEN_URL = "https://www.tumblr.com/oauth/request_token"
BASE_AUTH_URL = "https://www.tumblr.com/oauth/authorize"
ACCESS_TOKEN_URL = "https://www.tumblr.com/oauth/access_token"
REDIRECT_URI = 'https://www.programsinformationpeople.org/runestone/oauth'


def get_tokens(client_key=CLIENT_KEY, client_secret=CLIENT_SECRET,request_token_url=REQUEST_TOKEN_URL,base_authorization_url=BASE_AUTH_URL,access_token_url=ACCESS_TOKEN_URL,redirect_uri = REDIRECT_URI, verifier_auto=False):
    oauth_inst = requests_oauthlib.OAuth1Session(client_key,client_secret=client_secret)

    fetch_response = oauth_inst.fetch_request_token(request_token_url)

    # Using the dictionary .get method in these lines
    resource_owner_key = fetch_response.get('oauth_token')
    resource_owner_secret = fetch_response.get('oauth_token_secret')

    auth_url = oauth_inst.authorization_url(base_authorization_url)
    # Open the auth url in browser:
    webbrowser.open(auth_url) # For user to interact with & approve access of this app -- this script

    # Deal with required input, which will vary by API
    if verifier_auto: # if the input is default (True), like Twitter
        verifier = input("Please input the verifier:  ")
    else:
        redirect_result = input("Paste the full redirect URL here:  ")
        oauth_resp = oauth_inst.parse_authorization_response(redirect_result) # returns a dictionary -- you may want to inspect that this works and edit accordingly
        verifier = oauth_resp.get('oauth_verifier')

    # Regenerate instance of oauth1session class with more data
    oauth_inst = requests_oauthlib.OAuth1Session(client_key, client_secret=client_secret, resource_owner_key=resource_owner_key, resource_owner_secret=resource_owner_secret, verifier=verifier)

    oauth_tokens = oauth_inst.fetch_access_token(access_token_url) # returns a dictionary

    # Use that dictionary to get these things
    # Tuple assignment syntax
    resource_owner_key, resource_owner_secret = oauth_tokens.get('oauth_token'), oauth_tokens.get('oauth_token_secret')

    return client_key, client_secret, resource_owner_key, resource_owner_secret, verifier

def get_tokens_from_service(service_name_ident, expire_in_days=7): # Default: 7 days for creds expiration
    creds_data = get_from_cache(service_name_ident, CREDS_DICTION)
    if creds_data:
        if DEBUG:
            print("Loading creds from cache...")
            print()
    else:
        if DEBUG:
            print("Fetching fresh credentials...")
            print("Prepare to log in via browser.")
            print()
        creds_data = get_tokens()
        set_in_creds_cache(service_name_ident, creds_data, expire_in_days=expire_in_days)
    return creds_data

def create_request_identifier(url, params_diction, api_key = CLIENT_KEY):
    pd = params_diction
    blog_identifier = pd.pop('blog-identifier', None)
    method = pd.pop('method', None)
    if method == 'posts':
        posts_type = pd.pop('type', None)
        if posts_type:
            params_ident = "/".join([blog_identifier, method, posts_type])
        else:
            params_ident = "/".join([blog_identifier, method])
    # params_str = "_".join([str(e) for l in sorted_params for e in l]) # Make the list of tuples into a flat list using a complex list comprehension
    sorted_pd = sorted(pd.items(), key=lambda x:x[0])
    params_str =  "&".join(str(l[0]+"="+l[1]) for l in sorted_pd)
    total_ident = url + params_ident + "?api_key=" + str(api_key) + "&" + params_str
    return total_ident # Creating the identifier

def get_data_from_api(request_url,service_ident, params_diction, expire_in_days=7):
    """Check in cache, if not found, load data, save in cache and then return that data"""
    ident = create_request_identifier(request_url, params_diction)
    data = get_from_cache(ident,CACHE_DICTION)
    if data:
        if DEBUG:
            print("Loading from data cache: {}... data".format(ident))
    else:
        if DEBUG:
            print("Fetching new data from {}".format(ident))

        # Get credentials
        client_key, client_secret, resource_owner_key, resource_owner_secret, verifier = get_tokens_from_service(service_ident)

        # Create a new instance of oauth to make a request with
        oauth_inst = requests_oauthlib.OAuth1Session(client_key, client_secret=client_secret,resource_owner_key=resource_owner_key,resource_owner_secret=resource_owner_secret)
        # Call the get method on oauth instance
        # Work of encoding and "signing" the request happens behind the sences, thanks to the OAuth1Session instance in oauth_inst
        resp = oauth_inst.get(ident,params=params_diction)
        # Get the string data and set it in the cache for next time
        data_str = resp.text
        data = json.loads(data_str)
        set_in_data_cache(ident, data, expire_in_days)
    return data



####
## Define the TumblrPost Class:
class TumblrPost:
    def __init__(self, post_inst):
        self.blog_name = post_inst['blog_name']
        self.id = post_inst['id']
        self.url = post_inst['post_url']
        self.type = post_inst['type']
        self.num_tags = len(post_inst['tags'])
        if post_inst['summary']:
            self.summary = post_inst['summary']
        else:
            self.summary = ""
        self.slug = post_inst['slug'].replace('-', " ")
        self.time_posted = post_inst['date']

    def __str__(self):
        return "{0} | {1} | {2}".format(self.blog_name, self.type, self.url)


####
## Write CSV files
## Functions to convert Post instance to csv formatted row
def convert_to_csv(tumblr_post):
    tumblr_post_row_strings = [tumblr_post.url, tumblr_post.type, str(tumblr_post.num_tags), tumblr_post.slug.title(), tumblr_post.time_posted]
    csv_row_strings = []

    # Q: is there any better/simpler solution?
    for i in tumblr_post_row_strings:
        if i:
            if '"' in i:
                result = i.replace('"', '""')
                if ',' in i:
                    csv_row_strings.append('"' + result + '"')
                else:
                    csv_row_strings.append(result)
            else:
                if ',' in i:
                    csv_row_strings.append('"' + i + '"')
                else:
                    csv_row_strings.append(i)
        else:
            csv_row_strings.append("None")

    return csv_row_strings


def write_csv_resources(tumblr_posts, dir):
    outfile = open(dir, "w")  # dir is the directory of csv file
    header_columns = ["URL", "Type", "Number of Tags", "Title", "Time Posted"]  # define header
    outfile.write('{},{},{},{},{}\n'.format(*header_columns))  # no white space between attributes
    for post in tumblr_posts:
        outfile.write('{},{},{},{},{}\n'.format(*convert_to_csv(TumblrPost(post))))
    outfile.close()



if __name__ == "__main__":
    if not CLIENT_KEY or not CLIENT_SECRET:
        print("You need to fill in client_key and client_secret in the secret_data.py file.")
        exit()
    if not REQUEST_TOKEN_URL or not BASE_AUTH_URL:
        print("You need to fill in this API's specific OAuth2 URLs in this file.")
        exit()

    # Invoke functions
    tumblr_blog_baseurl = "https://api.tumblr.com/v2/blog/"
    tumblr_blog_params1 = {'blog-identifier': 'miova.tumblr.com', 'method':'posts', 'type': None, 'limit':'20'}
    tumblr_blog_params2 = {'blog-identifier': 'tcbunny.tumblr.com', 'method':'posts', 'type': None, 'limit':'20'}


    tumblr_result1 = get_data_from_api(tumblr_blog_baseurl,"Tumblr",tumblr_blog_params1) # Default expire_in_days
    # print(tumblr_result1)
    tumblr_result2 = get_data_from_api(tumblr_blog_baseurl,"Tumblr",tumblr_blog_params2) # Default expire_in_days
    # print(tumblr_result2)

    tumblr_posts1 = tumblr_result1['response']['posts']
    tumblr_posts2 = tumblr_result2['response']['posts']

    write_csv_resources(tumblr_posts1, "miova_tumblr_posts.csv")
    write_csv_resources(tumblr_posts2, "tcbunny_tumblr_posts.csv")


## Make sure to run your code and write CSV files by the end of the program.
