from PIL import Image, ImageDraw, ImageFont

# Create 1200x630 image with gradient-like blue background
img = Image.new('RGB', (1200, 630), color='#667eea')

# Add a subtle overlay
d = ImageDraw.Draw(img)

# Add border
d.rectangle([(40, 40), (1160, 590)], outline='white', width=6)

# Try to use a nice font, fallback to default
try:
    font_large = ImageFont.truetype('arial.ttf', 100)
    font_small = ImageFont.truetype('arial.ttf', 50)
except:
    font_large = ImageFont.load_default()
    font_small = ImageFont.load_default()

# Add main title
d.text((600, 240), 'QuizHub', fill='white', anchor='mm', font=font_large)

# Add subtitle
d.text((600, 380), 'AI-Powered Quiz Generator', fill='white', anchor='mm', font=font_small)

# Add call to action
d.text((600, 480), 'Create • Take • Learn', fill='#e0e7ff', anchor='mm', font=font_small)

# Save
img.save('static/media/quizhub-og-image.png')
print('✅ OG image created: static/media/quizhub-og-image.png')
print('   Size: 1200x630px')
print('   Ready for social media sharing!')
