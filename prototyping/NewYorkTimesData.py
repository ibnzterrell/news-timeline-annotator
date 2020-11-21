import requests
import json
import pandas as pd
import time

# Downloads last decade of NYT Headlines, 2010/1 - 2020/12
months = range(1, 13)
years = range(2010, 2021)
apiKey = "[API KEY]"

# exec(open("NewYorkTimesData.py").read())


def getMonthDataframe(month, year):
    print(f"Retrieving {year}/{month}")
    rawMonthData = requests.get(
        f"https://api.nytimes.com/svc/archive/v1/{year}/{month}.json?api-key={apiKey}")
    data = json.loads(rawMonthData.content)
    print("Retrieved. Processing Data.")
    # Drop Non-Articles
    df = pd.json_normalize(data["response"]["docs"])
    df = df[df["document_type"] == "article"]

    # Rename and Grab Columns We Want
    df["main_headline"] = df["headline.main"]
    df["print_headline"] = df["headline.print_headline"]

    # Split Keywords by Type
    df["people"] = [[obj["value"] for obj in kwlist if obj["name"] == "persons"]
                    for kwlist in df["keywords"]]
    df["organizations"] = [[obj["value"] for obj in kwlist if obj["name"]
                            == "organizations"] for kwlist in df["keywords"]]
    df["subjects"] = [[obj["value"] for obj in kwlist if obj["name"] == "subject"]
                      for kwlist in df["keywords"]]
    df["locations"] = [[obj["value"] for obj in kwlist if obj["name"]
                        == "glocations"] for kwlist in df["keywords"]]

    # df = df[["uri", "pub_date", "type_of_material", "main_headline", "print_headline", "lead_paragraph",
    #          "abstract", "keywords", "news_desk", "section_name", "subsection_name", "web_url"]]

    # NOTE: Changed due to lead_paragraph, abstract, and subsection_name missing from 2018/8 forward
    df = df[["uri", "pub_date", "type_of_material", "main_headline",
             "print_headline", "snippet", "news_desk", "section_name", "web_url", "people", "organizations", "subjects", "locations"]]

    # Drop Unlabled Material
    df = df.dropna(subset=["type_of_material"])

    # Drop Non-News Material
    # NOTE: Maybe include Text
    df = df[df["type_of_material"].isin(["News", "Brief", "Obituary (Obit)"])]

    # Drop News Desks that aren't about events
    df = df[~df['news_desk'].isin(["BookReview", "Podcasts", "Upshot"])]

    # Drop Sections that aren't about events or are subjective
    df = df[~df["section_name"].isin(["Opinion", "Fashion & Style"])]

    return df


dfs = []

for year in years:
    for month in months:
        # Skip December 2020 for now
        if (year == 2020 and month == 12):
            break
        mdf = getMonthDataframe(month, year)
        dfs.append(mdf)
        print(mdf)
        # NOTE NYT API has a rate limit of 10 requests per minute
        time.sleep(6)

dfs = pd.concat(dfs)
# The NYT API tends to return duplicates
dfs = dfs.drop_duplicates(subset=["uri"], keep="first")
dfs.to_csv("NYT_Data.csv", index=False, index_label=False)
