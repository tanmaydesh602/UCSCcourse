from bs4 import BeautifulSoup
import requests
import re
import textwrap
url = "https://catalog.ucsc.edu/en/current/general-catalog/courses/"
result = requests.get(url)
doc = BeautifulSoup(result.text, "html.parser")
course_links = [link["href"] for link in doc.find_all("ul", class_="sc-child-item-links")[0].find_all("a")]
class Course:
    def __init__(self, code, name, description, credits, gen_ed, prerequisites):
        self.code = code
        self.name = name
        self.credits = credits
        self.gen_ed = gen_ed

        # Separate description from prerequisites if concatenated
        description_text = description.decode('utf-8')
        if "Prerequisite(s):" in description_text:
            description_parts = description_text.split("Prerequisite(s):", 1)
            self.description = description_parts[0].strip().encode('utf-8')
            self.prerequisites = "Prerequisite(s): {}".format(description_parts[1].strip()).encode('utf-8')
        else:
            self.description = description.encode('utf-8')
            self.prerequisites = prerequisites.encode('utf-8') if prerequisites else None
    
    def __str__(self):
        course_info = "Code: {}\n".format(self.code)
        course_info += "Name: {}\n".format(self.name)
        
        # Decode description from UTF-8
        description_decoded = self.description.decode('utf-8')
        # Encode description to UTF-8 again
        description_encoded = description_decoded.encode('utf-8')
        course_info += "Description: {}\n".format(description_encoded)
        
        course_info += "Credits: {}\n".format(self.credits)
        
        if self.gen_ed:
            # Encode gen_ed to UTF-8
            gen_ed_encoded = self.gen_ed.encode('utf-8')
            course_info += "General Education Code: {}\n".format(gen_ed_encoded)
        
        if self.prerequisites:
            # Encode prerequisites to UTF-8
            prerequisites_encoded = self.prerequisites.encode('utf-8')
            # Check if prerequisites start with 'Prerequisite(s):'
            if prerequisites_encoded.startswith(b"Prerequisite(s):"):
                prerequisites_encoded = prerequisites_encoded.replace(b"Prerequisite(s):", b"", 1).strip()
            course_info += "Prerequisite(s): {}\n".format(prerequisites_encoded)
        
        return course_info
    
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
        name = name.encode('utf-8')
        description = description.encode('utf-8')
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

def print_course_info(course_list, course_code):
    found = False
    for course in course_list:
        if course.code == course_code:
            print(course)
            found = True
            break
    
    if not found:
        print("Course not found.")

# Assuming 'courses' is the list containing Course objects
# Let's say you want to print the information for course code 'CSE 3'
print_course_info(course_list, 'CMMU 102')


    
