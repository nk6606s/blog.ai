# OpenAI Blog & Image Generator  

This program provides an interface for generating high-quality blog content and AI-generated images using OpenAI's GPT and DALL·E models. It is designed for content creators, bloggers, and marketers who need automated, structured blog posts and AI-generated images for their platforms.  

## Features  

### 📝 Blog Content Generation  
- Generates blog posts in various formats such as:  
  - **Top 10 Lists**  
  - **Step-by-Step Guides**  
  - **Pros and Cons Analysis**  
  - **Case Studies**  
  - **How-To Tutorials**  
  - **Beginner’s Guides**  
  - **In-Depth Reviews**  
  - **Myths and Misconceptions**  
  - **Benefits Overviews**  
  - **Expert Opinions**  
- Uses structured Pydantic models to ensure well-formatted output.  
- Supports different content structures, including FAQs, checklists, real-world examples, and expert insights.  

### 🎨 Image Generation & Optimization  
- Generates AI-powered images using OpenAI's DALL·E 3.  
- Saves images in a structured directory format (`year/month`).  
- Compresses images to optimize storage while maintaining quality.  
- Supports image resizing using OpenCV.  

## 🚀 Usage  

### Blog Generation  
Call the function to generate structured content:  

```python
generate_blog_post(category="technology", blog_type="how-to", user_prompt="How to build a Python API")
