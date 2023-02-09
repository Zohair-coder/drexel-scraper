from bs4 import BeautifulSoup
import config.attributes as attributes


def parse(html, data: dict):

    soup = BeautifulSoup(html, "html.parser")
    table_rows = soup.find_all(attrs=attributes.rows)
    filter_out_headers(table_rows)

    # last row is empty
    table_rows.pop()

    for table_row in table_rows:
        row_data = table_row.find_all("td")

        row_data_strs = [fix_encoding_issue(
            data.text).strip() for data in row_data]

        crn = row_data_strs[5]

        data[crn].append({
            "subject_code": row_data_strs[0],
            "course_number": row_data_strs[1],
            "instruction_type": row_data_strs[2],
            "instruction_method": row_data_strs[3],
            "section": row_data_strs[4],
            "crn": row_data_strs[5],
            "course_title": row_data_strs[6],
            "days": row_data_strs[8],
            "times": row_data_strs[9],
            "instructor": row_data_strs[10],
        })

    return data


def fix_encoding_issue(text: str) -> str:
    return text.replace("\xa0", " ")


def filter_out_headers(rows):
    for row in rows:
        if row.find("th"):
            rows.remove(row)
