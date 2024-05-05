from bs4 import BeautifulSoup
import requests

class Course:
    def __init__(self, code, name, description, credits, gen_ed, prerequisites):
        self.code = code
        self.name = name
        self.credits = credits
        self.gen_ed = gen_ed

        # Remove non-breaking space (U+00A0) if present in description
        description = description.replace(u'\xa0', ' ')
        
        # Separate description from prerequisites if concatenated
        if "Prerequisite(s):" in description:
            description_parts = description.split("Prerequisite(s):", 1)
            self.description = description_parts[0].strip()
            self.prerequisites = "Prerequisite(s): {}".format(description_parts[1].strip())
        else:
            self.description = description
            self.prerequisites = prerequisites if prerequisites else None
    
    def __str__(self):
        course_info = "Code: {}\n".format(self.code)
        course_info += "Name: {}\n".format(self.name)
        course_info += "Description: {}\n".format(self.description)
        course_info += "Credits: {}\n".format(self.credits)
        if self.gen_ed:
            course_info += "General Education Code: {}\n".format(self.gen_ed)
        if self.prerequisites:
            course_info += "{}\n".format(self.prerequisites)
        return course_info

def print_course_info(course_list, course_code):
    found = False
    for course in course_list:
        if course.code == course_code:
            print(course)
            found = True
            break
    if not found:
        print("Course not found.")

url = "https://catalog.ucsc.edu/en/current/general-catalog/courses/"
result = requests.get(url)
doc = BeautifulSoup(result.text, "html.parser")
course_links = [link["href"] for link in doc.find_all("ul", class_="sc-child-item-links")[0].find_all("a")]

course_list = []
for link in course_links:
    course_url = "https://catalog.ucsc.edu{}".format(link)
    course_response = requests.get(course_url)
    course_soup = BeautifulSoup(course_response.content, "html.parser")
    course_entries = course_soup.find_all("h2", class_="course-name")
    for entry in course_entries:
        code = entry.find("span").string
        name = entry.find("span").find_next_sibling(text=True)[1:]

        desc_element = entry.find_next_sibling('div', class_='desc')
        p_tag = desc_element.find('p')

        if p_tag:
            description = p_tag.get_text().strip()
        else:
            description = desc_element.get_text().strip()

        code = str(code)
        name = name
        description = description
        description = '\n'.join(line.lstrip() for line in description.splitlines())

        credit_element = entry.find_next_sibling('div', class_='sc-credithours')
        credit = credit_element.find('div', class_='credits').get_text().strip()

        # Find the next course entry
        next_course = entry.find_next_sibling("h2", class_="course-name")

        gen_ed = None
        prerequisite = None
        current_sibling = entry.find_next_sibling()

        while current_sibling and current_sibling != next_course:
            if current_sibling.name == 'div':
                div_class = current_sibling.get('class')
                if div_class == ['genEd']:
                    gen_ed = current_sibling.find('p').get_text().strip()
                elif div_class == ['extraFields']:
                    req_heading = current_sibling.find('h4')
                    if req_heading and req_heading.get_text().strip() == 'Requirements':
                        prerequisite = current_sibling.find('p').get_text().strip()
            if gen_ed and prerequisite:
                break
            current_sibling = current_sibling.find_next_sibling()

        # Create a Course instance and add it to the list of course attributes
        tempcourse = Course(code, name, description, credit, gen_ed, prerequisite)
        course_list.append(tempcourse)

# Assuming 'courses' is the list containing Course objects
# Let's say you want to print the information for course code 'CMMU 102'
print_course_info(course_list, 'CSE 12')



    
