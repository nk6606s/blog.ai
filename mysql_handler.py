import mysql.connector
from datetime import datetime
import re

class MySQLHandler:
    def __init__(self, config):
        self.config = config
        self.connection = None

    def connect(self):
        try:
            self.connection = mysql.connector.connect(**self.config)
            if self.connection.is_connected():
                print("Connected to MariaDB")
        except mysql.connector.Error as err:
            print(f"Error connecting: {err}")

    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("MariaDB connection is closed")

    def get_next_unprocessed_term(self):
        cursor = self.connection.cursor()
        try:
            select_query = """
            SELECT term_id, name, z_category_description 
            FROM wp_terms 
            WHERE term_id >= 89 
            AND z_processed = FALSE 
            AND z_category_description != '' 
            LIMIT 1
            """
            cursor.execute(select_query)
            record = cursor.fetchone()

            if record:
                term_id, name, z_category_description = record
                return term_id, name, z_category_description
            else:
                update_query = "UPDATE wp_terms SET z_processed = FALSE WHERE term_id >= 89 AND z_category_description != ''"
                cursor.execute(update_query)
                self.connection.commit()

                cursor.execute(select_query)
                updated_record = cursor.fetchone()

                if updated_record:
                    term_id, name, z_category_description = updated_record
                    return term_id, name, z_category_description
                else:
                    return None, None, None

        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return None, None, None
        finally:
            cursor.close()

    def get_blog_template(self, z_category_description):
        cursor = self.connection.cursor()
        try:
            select_query = """
                SELECT blog_type, user_prompt 
                FROM blog_templates 
                WHERE is_taken = FALSE 
                ORDER BY RAND() 
                LIMIT 1
            """
            cursor.execute(select_query)
            record = cursor.fetchone()

            if record:
                blog_type, user_prompt = record  # Extract values directly from the tuple

                # Replace '{category}' with the given z_category_description
                user_prompt = user_prompt.replace("{category}", z_category_description)

                return blog_type, user_prompt
            else:
                # Reset all prompts to is_taken = FALSE
                update_query = "UPDATE blog_templates SET is_taken = FALSE"
                cursor.execute(update_query)
                self.connection.commit()

                cursor.execute(select_query)  # Retry selecting a user prompt
                updated_record = cursor.fetchone()

                if updated_record:
                    blog_type, user_prompt = updated_record  # Extract values directly from the tuple

                    # Replace '{category}' with the given z_category_description
                    user_prompt = user_prompt.replace("{category}", z_category_description)

                    return blog_type, user_prompt
                else:
                    return None, None  # Return None for both values if no record found

        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return None, None  # Return None for both values on error
        finally:
            cursor.close()

    def mark_blog_type_as_taken(self, blog_type: str):
        cursor = self.connection.cursor()
        try:
            # Update the is_taken status to TRUE for the specified blog_type
            update_query = """
            UPDATE blog_templates 
            SET is_taken = TRUE 
            WHERE blog_type = %s
            """
            cursor.execute(update_query, (blog_type,))
            self.connection.commit()

            # Check how many rows were updated
            if cursor.rowcount > 0:
                print(f"Successfully updated {cursor.rowcount} rows to is_taken = TRUE for blog_type: {blog_type}.")
            else:
                print("No rows were updated. Check if the blog_type exists.")

        except mysql.connector.Error as err:
            print(f"Error: {err}")
        finally:
            cursor.close()

    def create_blog_post(self, blog_content):

        def generate_slug(title: str) -> str:
            # Remove all special characters except for letters, numbers, and spaces
            slug = re.sub(r'[^a-zA-Z0-9\s]', '', title)

            # Replace spaces with hyphens
            slug = slug.replace(" ", "-")

            # Limit the length to 200 characters
            if len(slug) > 200:
                slug = slug[:200]

            return slug

        if not self.connection:
            print("No active connection to MariaDB")
            return

        cursor = self.connection.cursor()

        try:
            post_title = blog_content["title"]
            post_content = blog_content["content"]
            post_status = "publish"
            post_parent = 0
            post_type = "post"
            post_author = 1
            post_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            post_excerpt = ""
            post_name = generate_slug(blog_content["title"])
            to_ping = ""
            pinged = ""
            post_content_filtered = ""

            insert_query = """
            INSERT INTO wp_posts (
                post_author, post_date, post_content, post_title, post_status, 
                post_name, post_parent, post_type, post_modified, post_modified_gmt, 
                post_excerpt, to_ping, pinged, post_content_filtered
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            post_data = (
                post_author, post_date, post_content, post_title, post_status, post_name, post_parent, post_type,
                post_date, post_date, post_excerpt, to_ping, pinged, post_content_filtered
            )

            cursor.execute(insert_query, post_data)
            post_id = cursor.lastrowid

            self.connection.commit()
            print(f"Blog post created with ID: {post_id}")
            return post_id

        except mysql.connector.Error as err:
            print(f"Error: {err}")
            self.connection.rollback()
        finally:
            cursor.close()

    def create_image_attachment(self, image_name: str, post_id: int, month: str, year: str):
        """Create an image attachment in the wp_posts table."""

        if not self.connection:
            print("No active connection to MariaDB")
            return

        cursor = self.connection.cursor()

        try:
            # Prepare the post title and post name
            post_title = image_name.rsplit('.', 1)[0]  # Using the image name as post title
            post_name = image_name.rsplit('.', 1)[0].lower()  # Remove the extension for post_name
            post_status = "inherit"  # As specified
            comment_status = "open"  # As specified
            ping_status = "closed"  # As specified
            guid = f"https://chillandearn.com/wp-content/uploads/{year}/{month}/{image_name}"  # Construct GUID
            post_mime_type = "image/jpeg"  # As specified
            post_type = "attachment"  # As specified
            post_parent = post_id  # Using input parameter post_id
            post_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Current date

            insert_query = """
            INSERT INTO wp_posts (
                post_author, post_date, post_content, post_title, post_status, 
                post_name, post_parent, post_type, post_modified, post_modified_gmt, 
                post_excerpt, to_ping, pinged, post_content_filtered, guid, post_mime_type
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            # Post data to insert
            post_data = (
                1,  # Assuming the author ID is 1
                post_date,  # post_date
                "",  # post_content (not needed for attachments)
                post_title,  # post_title
                post_status,  # post_status
                post_name,  # post_name without extension
                post_parent,  # post_parent
                post_type,  # post_type
                post_date,  # post_modified
                post_date,  # post_modified_gmt
                "",  # post_excerpt
                "",  # to_ping
                "",  # pinged
                "",  # post_content_filtered
                guid,  # guid
                post_mime_type  # post_mime_type
            )

            cursor.execute(insert_query, post_data)
            attachment_id = cursor.lastrowid

            self.connection.commit()
            print(f"Image attachment created with ID: {attachment_id}")
            return attachment_id

        except mysql.connector.Error as err:
            print(f"Error: {err}")
            self.connection.rollback()
        finally:
            cursor.close()

    def assign_category_to_post(self, category_id, post_id):
        """Assign a category to a post in the wp_term_relationships table."""
        term_order = 0
        insert_query = """
            INSERT INTO wp_term_relationships (object_id, term_taxonomy_id, term_order)
            VALUES (%s, %s, %s)
        """
        category_data = (post_id, category_id, term_order)

        cursor = self.connection.cursor()
        try:
            cursor.execute(insert_query, category_data)
            self.connection.commit()
            print(f"Category ID {category_id} assigned to Post ID {post_id}.")
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            self.connection.rollback()
        finally:
            cursor.close()

    def update_term_processed(self, term_id: int):
        """Update the z_processed column to true in the wp_terms table based on the term_id."""
        update_query = """
            UPDATE wp_terms
            SET z_processed = TRUE
            WHERE term_id = %s
        """

        cursor = self.connection.cursor()
        try:
            cursor.execute(update_query, (term_id,))
            self.connection.commit()
            print(f"Term ID {term_id} updated to z_processed = TRUE.")
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            self.connection.rollback()
        finally:
            cursor.close()

    def assign_image_to_post(self, post_id: int, post_attachment_id: int, image_path: str):
        """Assign image details to a post in the wp_postmeta table."""

        cursor = self.connection.cursor()

        try:
            # Insert the _thumbnail_id record
            insert_thumbnail_query = """
            INSERT INTO wp_postmeta (post_id, meta_key, meta_value) 
            VALUES (%s, %s, %s)
            """

            thumbnail_data = (post_id, '_thumbnail_id', post_attachment_id)
            cursor.execute(insert_thumbnail_query, thumbnail_data)

            # Insert the image_path record
            insert_image_path_query = """
            INSERT INTO wp_postmeta (post_id, meta_key, meta_value) 
            VALUES (%s, %s, %s)
            """

            image_path_data = (post_attachment_id, '_wp_attached_file', image_path)
            cursor.execute(insert_image_path_query, image_path_data)

            # Commit the changes
            self.connection.commit()
            print(
                f"Image assigned to Post ID {post_id} with attachment ID {post_attachment_id} and image path '{image_path}'.")

        except mysql.connector.Error as err:
            print(f"Error: {err}")
            self.connection.rollback()
        finally:
            cursor.close()

# Usage Example
if __name__ == "__main__":
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

    # Create a blog post example
    blog_content = {
        "title": "Your Blog Title Here",
        "content": "This is the content of your blog post.",
        "excerpt": "This is a short excerpt."
    }
    post_id = db_handler.create_blog_post(blog_content)

    # Assign the category to the post
    if post_id:
        db_handler.assign_category_to_post(category_id=term_id, post_id=post_id)

    # Close the database connection
    db_handler.close()
