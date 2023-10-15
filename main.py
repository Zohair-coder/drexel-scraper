from scrape import scrape

import json
import sys
import time
import os
import cProfile
import traceback

def main():
    0/0 # added for testing purposes
    start_time = time.time()

    include_ratings = False
    if "--ratings" in sys.argv:
        include_ratings = True

    all_colleges = False
    if "--all-colleges" in sys.argv:
        all_colleges = True

    data = scrape(include_ratings=include_ratings, all_colleges=all_colleges)

    assert len(data) > 0, "No data found"

    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

    print("Found {} items".format(len(data)))
    print("Data written to data.json")


    if "--db" in sys.argv:
        print("Time taken to scrape data: {} seconds".format(time.time() - start_time))
        print()
        import db
        print("Updating database...")
        db.populate_db(data)

    print("Done!")

    print("--- {} seconds ---".format(time.time() - start_time))

if __name__ == "__main__":

    try:
        if not os.path.exists("performance"):
            os.makedirs("performance")
        cProfile.run("main()", "performance/profile_output.pstat")
    except Exception as e:
        trace = traceback.format_exc()
        print(trace)
        
        if "--email" in sys.argv:
            import emailer
            if emailer.send_email("Error running scraper", trace):
                print("Exeception email sent")
            else:
                print("Error sending exception email")

