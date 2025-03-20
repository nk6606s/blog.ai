# 1. Query table and check category to be processed
# 2. Generate feature image and upload to /var/www/html/wp-content/uploads/yyyy/mm
# 3. Call generate_blog, based on category
# 4. Insert blog into posts table.
# 5. Insert attachment record into posts table.
# 6. Insert entry into wp_postmeta table.

from mysql_handler import MySQLHandler  # Assuming the class is in a file named mysql_handler.py
from openai_handler import OpenAIHandler
from blog_parser import BlogContentParser
from datetime import datetime
import json
import re
import os

config = {
    'user': 'XXX',
    'password': 'XXX',
    'host': 'XXX',  # AWS public IP of the instance
    'database': 'XXX',
    'port': 'XXX'
}

# Initialize MySQLHandler
db_handler = MySQLHandler(config)

# Connect to the database
db_handler.connect()

# Get next unprocessed term (term_id, name, z_category_description)
term_id, name, z_category_description = db_handler.get_next_unprocessed_term()

blog_type, user_prompt = db_handler.get_blog_template(z_category_description=z_category_description)

# print(blog_type, user_prompt)

# print(term_id)
if term_id:
    print(f"Next unprocessed Term: ID={term_id}, Name={name}, Description={z_category_description}")
else:
    print("Error: No term could be fetched.")

# Close the database connection
db_handler.close()

# Initialize OpenAI handler with your API key
api_key = "XXX"
openai_handler = OpenAIHandler(api_key=api_key)

# Call the method to generate blog content with the specified category
blog_content_json = openai_handler.generate_blog_post(category=z_category_description, blog_type=blog_type, user_prompt=user_prompt)

# print(blog_content_json)

blog_content = json.loads(blog_content_json)

# Instantiate the parser and parse the blog content
parser = BlogContentParser(blog_content_json=blog_content_json, blog_type=blog_type, category=z_category_description, openai_handler=openai_handler, save_path="/var/www/html/wp-content/uploads")
title, html_content = parser.parse_blog()

# Print the title and HTML content
print("Title:", title)
# print("\nHTML Content:\n", html_content)

# Initialize the MySQL handler
mysql_handler = MySQLHandler(config=config)

# Connect to the database
mysql_handler.connect()

# Create the blog post in the database using the generated title and content
post_id = mysql_handler.create_blog_post({
    "title": title,
    "content": html_content
})

# mark blog template used
mysql_handler.mark_blog_type_as_taken(blog_type=blog_type)

# Assign a category to the newly created post
mysql_handler.assign_category_to_post(category_id=term_id, post_id=post_id)
mysql_handler.update_term_processed(term_id=term_id)

# Generate an image with a specific prompt
prompt = name  # Assuming `name` is defined elsewhere in your code
save_path = "/var/www/html/wp-content/uploads"
# save_path = ""

# Get current month and year
current_month = datetime.now().strftime("%m")  # Current month as a two-digit number
current_year = datetime.now().strftime("%Y")   # Current year as a four-digit number

image_file_path = openai_handler.generate_image(prompt, save_path, current_month, current_year)

# print(image_file_path)
attachment_id = mysql_handler.create_image_attachment(os.path.basename(image_file_path), post_id, current_month, current_year)
mysql_handler.assign_image_to_post(post_id, attachment_id, image_file_path)

# Close the database connection
db_handler.close()