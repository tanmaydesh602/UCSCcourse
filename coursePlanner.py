import requests
from bs4 import BeautifulSoup
import pickle
import os.path
import networkx as nx
import matplotlib.pyplot as plt
import re


# Define the Course class
class Course:
    def __init__(self, code, name, description, credits, gen_ed, prerequisites):
        self.code = code
        self.name = name
        self.description = description
        self.credits = credits
        self.gen_ed = gen_ed
        self.prerequisites = prerequisites

    def __str__(self):
        return self.code

# Define the scrape_course_info function
def scrape_course_info():
    url = "https://catalog.ucsc.edu/en/current/general-catalog/courses/"
    result = requests.get(url)
    doc = BeautifulSoup(result.text, "html.parser")
    course_links = [link["href"] for link in doc.find_all("ul", class_="sc-child-item-links")[0].find_all("a")]

    course_list = []
    prerequisites_map = {}  # Dictionary to store prerequisites for each course

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
            prerequisites = {}
            current_sibling = entry.find_next_sibling()

            while current_sibling and current_sibling != next_course:
                if current_sibling.name == 'div':
                    div_class = current_sibling.get('class')
                    if div_class == ['genEd']:
                        gen_ed = current_sibling.find('p').get_text().strip()
                    elif div_class == ['extraFields']:
                        req_heading = current_sibling.find('h4')
                        if req_heading:
                            req_type = req_heading.get_text().strip()
                            req_content = current_sibling.find('p').get_text().strip().split(';')
                            prerequisites[req_type] = [req.strip() for req in req_content]
                current_sibling = current_sibling.find_next_sibling()

            # Create a Course instance and add it to the list of course attributes
            tempcourse = Course(code, name, description, credit, gen_ed, prerequisites)
            course_list.append(tempcourse)

            # Store prerequisites in the prerequisites map
            prerequisites_map[code] = prerequisites

    # Save the course list and prerequisites map to files
    with open('course_list.pkl', 'wb') as f:
        pickle.dump(course_list, f)
    with open('prerequisites_map.pkl', 'wb') as f:
        pickle.dump(prerequisites_map, f)

    return course_list, prerequisites_map

# Define the load_course_info function
def load_course_info():
    if os.path.exists('course_list.pkl') and os.path.exists('prerequisites_map.pkl'):
        with open('course_list.pkl', 'rb') as f1, open('prerequisites_map.pkl', 'rb') as f2:
            return pickle.load(f1), pickle.load(f2)
    else:
        return scrape_course_info()

# Define a function to create a graph from course prerequisites
def create_course_graph(course_code, prerequisites_map):
    G = nx.DiGraph()

    # Recursively add prerequisites and their connections
    def add_prerequisites(course_code, visited=set()):
        if course_code not in prerequisites_map or course_code in visited:
            return
        visited.add(course_code)
        if isinstance(prerequisites_map[course_code], list):
            prereq_courses = prerequisites_map[course_code]
            for prereq_course in prereq_courses:
                # Remove any additional text from the course code
                prereq_course_code = re.findall(r'[A-Z]+\s\d+', prereq_course)[0]
                G.add_edge(prereq_course_code, course_code)  # Add edge from prerequisite to the course
                add_prerequisites(prereq_course_code, visited)  # Recursively add prerequisites
        else:
            for prereq_type, prereq_courses in prerequisites_map[course_code].items():
                for prereq_course in prereq_courses:
                    # Remove any additional text from the course code
                    prereq_course_code = re.findall(r'[A-Z]+\s\d+', prereq_course)[0]
                    G.add_edge(prereq_course_code, course_code)  # Add edge from prerequisite to the course
                    add_prerequisites(prereq_course_code, visited)  # Recursively add prerequisites

    add_prerequisites(course_code)
    return G

# Load course information and prerequisites map
course_list, prerequisites_map = load_course_info()

# Specify the course code you want to visualize
course_code = 'CSE 101'

# Create a graph for the specified course and its prerequisites
course_graph = create_course_graph(course_code, prerequisites_map)

# Draw the graph
plt.figure(figsize=(10, 6))
pos = nx.spring_layout(course_graph)  # Layout for better visualization
nx.draw(course_graph, pos, with_labels=True, node_size=1500, node_color='skyblue', font_size=10, font_weight='bold', arrowsize=20)
plt.title("Course Prerequisites Graph for {}".format(course_code))
plt.show()
