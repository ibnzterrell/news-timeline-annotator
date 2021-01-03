import time
import pandas as pd
import json
import requests

# Downloads last decade of NYT Headlines, 2010/1 - 2020/12
months = range(1, 13)
years = range(1851, 2021)
apiKey = "[API KEY]"

# python -u .\NewYorkTimesData.py


def getMonthDataframe(month, year):
    print(f"Retrieving {year}-{month}")
    rawMonthData = requests.get(
        f"https://api.nytimes.com/svc/archive/v1/{year}/{month}.json?api-key={apiKey}")
    data = json.loads(rawMonthData.content)
    print("Retreived. Processing Month.")

    # Convert JSON to Dataframe
    df = pd.json_normalize(data["response"]["docs"])

    # Some months are missing, don't process those
    if df.empty:
        print(f"Missing Month: {year}-{month}")
        return df

    # Drop Non-Articles
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

    # Drop Unlabeled Material
    df = df.dropna(subset=["type_of_material"])

    # Drop Non-News Material
    # NOTE: Older material is under Archives
    df = df[df["type_of_material"].isin(
        ["Archives", "News", "Brief", "Obituary (Obit)"])]

    # Drop News Desks that aren't event headlines
    df = df[~df['news_desk'].isin(["BookReview", "Podcasts", "Upshot"])]

    # Drop Sections that typically aren't about singular events
    df = df[~df["section_name"].isin(["Opinion", "Fashion & Style"])]

    # Visual Sanity Check
    print(df[["pub_date", "main_headline"]])
    return df


dfs = []

for year in years:
    for month in months:
        mdf = getMonthDataframe(month, year)
        dfs.append(mdf)
        # NOTE NYT API has a rate limit of 10 requests per minute
        time.sleep(6)

print("Concatenating")
dfs = pd.concat(dfs)
# The NYT API tends to return duplicates
print("Dropping Duplicates")
dfs = dfs.drop_duplicates(subset=["uri"], keep="first")
print(dfs)
print("Writing to CSV")
dfs.to_csv("NYT_Data.csv", index=False, index_label=False)
