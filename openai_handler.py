# openai_handler.py
import os
from datetime import datetime

import requests
from pydantic import BaseModel
from typing import List, Dict
from openai import OpenAI
from PIL import Image
import cv2

# Define the response model using Pydantic
class BlogSection(BaseModel):
    heading: str  # Each section will have a heading
    content: str  # Each section will have a detailed explanation

class BlogContent(BaseModel):
    title: str
    intro: str
    sections: List[BlogSection]  # Now each section has a heading and content
    conclusion: str


class RealWorldExample(BaseModel):
    title: str
    description: str  # Description of the example
    impact: str  # Outcome or impact of the example

class Statistic(BaseModel):
    description: str
    value: str

class FAQItem(BaseModel):
    question: str
    answer: str
class ChecklistItem(BaseModel):
    item: str  # Description of the checklist item
    is_completed: bool

class Top10BlogContent(BaseModel):
    title: str
    intro: str
    sections: List[BlogSection]  # Each tool will have a heading and content
    conclusion: str

class StepByStepGuideContent(BaseModel):
    title: str
    intro: str
    steps: List[BlogSection]  # Each step will have a heading and content
    conclusion: str

class ProsAndConsContent(BaseModel):
    title: str
    intro: str
    pros: List[BlogSection]  # Each pro will have a heading and content
    cons: List[BlogSection]  # Each con will have a heading and content
    conclusion: str

class CaseStudyContent(BaseModel):
    title: str
    intro: str
    challenges: List[BlogSection]  # Each challenge will have a heading and content
    strategies: List[BlogSection]  # Each strategy will have a heading and content
    outcomes: List[BlogSection]  # Each outcome will have a heading and content
    insights: List[BlogSection]  # Each insight will have a heading and content
    conclusion: str

class HowToTutorialContent(BaseModel):
    title: str
    intro: str
    prerequisites: List[BlogSection]
    tools_needed: List[BlogSection]
    steps: List[BlogSection]
    checklist: List[ChecklistItem]
    tips: List[BlogSection]
    faqs: List[BlogSection]
    conclusion: str

class BeginnersGuideContent(BaseModel):
    title: str
    intro: str
    prerequisites: List[BlogSection]
    key_concepts: List[BlogSection]
    examples: List[BlogSection]
    step_by_step_tutorial: List[BlogSection]
    common_mistakes: List[BlogSection]
    faqs: List[BlogSection]
    further_reading: List[BlogSection]
    conclusion: str

class InDepthReviewContent(BaseModel):
    title: str
    intro: str
    features: List[BlogSection]  # Each feature will have a heading and content
    benefits: List[BlogSection]  # Each benefit will have a heading and content
    drawbacks: List[BlogSection]  # Each drawback will have a heading and content
    conclusion: str

class MythsAndMisconceptionsContent(BaseModel):
    title: str
    intro: str
    myths: List[BlogSection]  # Each myth will have a heading and content
    conclusion: str


class BenefitsOverviewContent(BaseModel):
    title: str
    intro: str
    benefits: List[BlogSection]  # Core section listing benefits
    use_cases: List[RealWorldExample]  # Real-world examples showing the benefits in action
    statistics: List[Statistic]  # Supporting data to back up benefits
    potential_drawbacks: List[BlogSection]  # Honest discussion of any potential cons or limitations
    comparison_with_alternatives: List[BlogSection]  # Compare the benefits to other similar options
    faqs: List[FAQItem]  # Frequently asked questions to clarify common queries
    tips_for_maximizing_benefits: List[BlogSection]  # Tips on how to leverage these benefits most effectively
    conclusion: str


class ExpertQuote(BaseModel):
    expert_name: str  # Name of the expert
    expert_title: str  # Title or position of the expert
    organization: str  # Organization the expert is affiliated with
    quote: str  # The expert's opinion or insight
    context: str  # Optional context to give background for the quote


class ExpertOpinionsContent(BaseModel):
    title: str
    intro: str
    expert_quotes: List[ExpertQuote]  # List of detailed expert quotes
    themes: List[str]  # Key themes or takeaways from the expert quotes
    further_reading: List[str]
    conclusion: str

# Define OpenAIHandler class
class OpenAIHandler:
    def __init__(self, api_key):
        # Initialize OpenAI client with the provided API key
        self.client = OpenAI(api_key=api_key)

    def generate_blog_post(self, category: str, blog_type: str, user_prompt: str) -> str:
        """Generate a blog post with a given category using OpenAI."""
        # Call the OpenAI API for blog generation
        resp_format = "BlogContent"
        if blog_type == "top_10_list":
            resp_format = Top10BlogContent
        if blog_type == "step_by_step_guide":
            resp_format = StepByStepGuideContent
        if blog_type == "pros_and_cons":
            resp_format = ProsAndConsContent
        if blog_type == "case_study":
            resp_format = CaseStudyContent
        if blog_type == "how_to_tutorial":
            resp_format = HowToTutorialContent
        if blog_type == "beginners_guide":
            resp_format = BeginnersGuideContent
        if blog_type == "in_depth_review":
            resp_format = InDepthReviewContent
        if blog_type == "myths_and_misconceptions":
            resp_format = MythsAndMisconceptionsContent
        if blog_type == "benefits_overview":
            resp_format = BenefitsOverviewContent
        if blog_type == "expert_opinions":
            resp_format = ExpertOpinionsContent


        completion = self.client.beta.chat.completions.parse(
            model="gpt-4o-mini",  # Adjust the model if needed
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert blog writer with a deep understanding of finance, technology, and investment strategies. Your task is to create highly engaging and informative content for an audience interested in passive income opportunities."
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            response_format=resp_format,  # Parse response directly into the Pydantic model
        )

        # Extract the parsed BlogContent model (no need to manually subscript)
        blog_content_json = completion.choices[0].message.content

        # print(blog_content_json)

        # Return the structured blog content
        return blog_content_json
        # return user_prompt

    def generate_image(self, prompt: str, save_path: str, month: str, year: str):
        """Generate an image using OpenAI API, save it, and compress the image."""
        # Create directory if it does not exist
        full_path = os.path.join(save_path, year, month)
        os.makedirs(full_path, exist_ok=True)

        try:
            # Call OpenAI API to generate the image
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )

            # Get the image URL from the response
            image_url = response.data[0].url

            # Download the image
            image_data = requests.get(image_url).content

            # Create a valid filename by removing spaces and special characters
            safe_prompt = prompt.replace("&amp;", "").replace(" ", "_")  # Replace spaces with underscores
            timestamp = int(datetime.now().timestamp())  # Get current timestamp
            image_file_name = f"{safe_prompt}_{timestamp}.jpg"  # Construct the filename as .jpg

            # Specify the full image path where you want to save the image
            image_file_path = os.path.join(full_path, image_file_name)

            # Save the image to the specified path (as JPEG first)
            with open(image_file_path, 'wb') as handler:
                handler.write(image_data)

            # print(f"Image saved to {image_file_path}")

            # Compress the saved image
            self.compress_image(image_file_path, quality=70)

            # print(f"Compressed image saved to {image_file_path}")  # Confirm it's the same path
            return image_file_path  # Return the path for further processing if needed

        except Exception as e:
            print(f"An error occurred while generating the image: {e}")
            return None

    @staticmethod
    def compress_image(input_image_path, quality=70):
        """Compress the image using Pillow and overwrite the original."""
        try:
            # Open the image file
            with Image.open(input_image_path) as img:
                # Convert to RGB and save as JPEG, overwriting the original file
                img.convert('RGB').save(input_image_path, 'JPEG', optimize=True, quality=quality)
            print(f"Image compressed and saved to {input_image_path}")
        except Exception as e:
            print(f"An error occurred while compressing the image: {e}")

    @staticmethod
    def resize_image_opencv(input_image_path, output_size=(256, 256)):
        """Resize the image using OpenCV.

        Args:
            input_image_path: Path to the input image file.
            output_size: Target size of the resized image (width, height) as a tuple. Defaults to (512, 512).
        """
        img = cv2.imread(input_image_path)
        resized_img = cv2.resize(img, output_size)
        cv2.imwrite(input_image_path, resized_img)
