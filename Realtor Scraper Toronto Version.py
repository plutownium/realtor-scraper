import requests
from bs4 import BeautifulSoup
import time
import csv
import json

# url_r = 'https://www.realtor.ca/realtor-search-results#city=burnaby&province=3&page=1&sort=11-A'
# url_b = "https://www.realtor.ca/"
# Goal: Secure a JSON Result from the realtor.ca website.
# Goal achieved.


headers = {
    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"
}

cookies = {"ai_user": "2CQf5|2019-05-02T21:30:06.440Z",
           "DG_ZID": "E6531F5F-9DAD-318F-96B1-96B45F3AACF5",
           "DG_ZUID": "DB91DEE1-F6F9-3D7A-9C6E-FC3BCA87E059",
           "DG_HID": "4D995F1A-292A-3DC1-9A4F-BF06D51BA507",
           "DG_SID": "50.68.164.37:jQWOy8HWHOoNzHVP+JeAGURzEcpMW1Ll3W2dVqTbyx8",
           "Language": "1", "app_mode": "1",
           "Province": "British Columbia",
           "Country": "Canada",
           "GUID": "c677b803-5bf1-4db8-bcc0-414b8e06e433",
           "gig_hasGmid": "ver2",
           "__AntiXsrfToken": "1ef614cd4a754a638bb427d9abdc9693",
           "cmsdraft": "False",
           "DG_IID": "7D66C09A-4D91-37AE-9228-C51FC33E29DB",
           "DG_UID": "B1FB1708-05F2-3553-A395-A6F2F329FD19"}

THE_URL = "https://www.realtor.ca/Services/ControlFetcher.asmx/GetRealtorResults"

payload_json = {"firstName":"", "lastName":"", "addressLine1":"",
                "city":"richmond", "companyName":"",
                "designations":"", "languages":"", "postalCode":"", "provinceIds":"3", "specialties":"", "isCCCMember":"",
                "currentPage":"190", "sortBy":"11", "sortOrder":"A", "organizationId":"",
                "recordsPerPage": 50, "maxRecords": None, "showOfficeDetails": None}  # provinceIds: 3

ontario_payload = {"firstName":"", "lastName":"", "addressLine1":"",
                "city":"mississauga", "companyName":"",
                "designations":"", "languages":"", "postalCode":"", "provinceIds":"2", "specialties":"", "isCCCMember":"",
                "currentPage":"190", "sortBy":"11", "sortOrder":"A", "organizationId":"",
                "recordsPerPage": 50, "maxRecords": None, "showOfficeDetails": None}  # provinceIds: 2


r = requests.post(THE_URL, json=payload_json, headers=headers, cookies=cookies)
print(r.status_code)
time.sleep(5)
json_result = str(r.json())  # json encoded as HTML; a very long string

iterator = 1

realtor_names = []
realtor_contact_nums = []
office_addresses = []
office_names = []
titles_realtors = []

for i in range(1, 200):
    ontario_payload["currentPage"] = str(i)  # Change current pg to 1-21
    # insert the updated json payload into the post request
    looped_request = requests.post(THE_URL, json=ontario_payload, headers=headers, cookies=cookies)

    # check if we received a 200 response, if not, print the code and break the loop
    if str(looped_request.status_code) != "200":
        # Make a nice record log of what went wrong
        print(looped_request.status_code)
        to_save = "Failure status code: " + str(looped_request.status_code)
        recordlog = open("failure{}.txt".format(i), "w")
        recordlog.write(to_save)
        recordlog.write(json.dumps(payload_json))
        recordlog.close()

        time.sleep(10)
        # Sleep then make the post request again... Just try it...
        looped_request = requests.post(THE_URL, json=ontario_payload, headers=headers, cookies=cookies)

        if str(looped_request.status_code) != "200":
            # Make a nice record log of what went wrong
            print(looped_request.status_code)
            to_save = "2nd Failure status code: " + str(looped_request.status_code)
            recordlog = open("failure again {}.txt".format(i + 1), "w")
            recordlog.write(to_save)
            recordlog.write(json.dumps(payload_json))
            recordlog.close()
        break

    time.sleep(5)  # Be nice to the server
    print("Going: " + str(i))
    jresult = str(looped_request.json())  # Change the request into readable stuff

    #
    #
    # Prepare the soup for data extraction
    soup = BeautifulSoup(jresult, "html.parser")  # More work to make it readable

    a = soup.find_all("span", {"class": "realtorCardName"})
    for item in a:
        # Just the names, not the surrounding "span" tag
        realtor_names.append(item.contents[0])

    with_some_garbage = soup.find_all("span", {"class": "realtorCardContactNumber"})
    for k in with_some_garbage:
        if "Website" not in str(k):
            # Just the numbers, not the surrounding "span" tag
            realtor_contact_nums.append(k.contents[0])

    addys = soup.find_all("div", {"class": "realtorCardOfficeAddress"})
    for addy in addys:
        as_txt = str(addy.contents)[38:]
        cleaned_up = as_txt.split("   ")[0][0:-6]
        office_addresses.append(cleaned_up.strip())

    names_offices = soup.find_all("div", {"class": "realtorCardOfficeName"})
    for k in names_offices:
        as_txt = str(k.contents)[38:].split("   ")[0][:-6]
        office_names.append(as_txt.strip())

    rtitles = soup.find_all("div", {"class": "realtorCardTitle"})

    for k in rtitles:
        as_txt = str(k.contents)
        if len(as_txt) > 10:
            # Remove the junk on either side of Personal Real Estate Corp
            cleaned_up_title = as_txt[34:].split("   ")[0][:-6]
            titles_realtors.append(cleaned_up_title.strip())
        else:  # Note: Removed some junk here
            titles_realtors.append(str(iterator) + ". No Title")
        iterator += 1


rows = zip(realtor_names, realtor_contact_nums, office_addresses, office_names, titles_realtors)

with open("realtors-Mississauga.csv", "w") as csvFile:
    writer = csv.writer(csvFile)
    for row in rows:
        writer.writerow(row)

csvFile.close()

print("Success!")


# Notes: I can do 50 recordsPerPage and still get a result. I can't do 65 resultsPerPage.
# Vancouver: 9,468 realtors
# North Vancouver: 980 / 50 = 19.6
# West Vancouver: 872 ~ 17.44
# Burnaby: 1,701 ~ 34
# New West: 235 / 50 = 4.70
# Langley: 772 ~ 15.48
# Richmond: 2,006 ~ 40.12

# ONTARIO:
# Mississauga: 10,003 ~ 200 pg
# Toronto: 21,750 ~ 435 pages
# Vaughan: 1,573 ~ 31.46
# Hamilton: 1,147 ~ 22.94
# Brampton: 4,660 ~ 93.2
# Richmond Hill: 3,652 ~ 73
# Pickering: 268
# Milton: 1,752 ~ 35
# Oakville: 2,078 ~ 41.56
