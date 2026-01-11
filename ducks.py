#!/usr/bin/env python3

import yaml
from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path
import math


def create_duck_cell(image_path, subtitle, font, text_color, stroke_color):
    img = Image.open(image_path)
    
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    padding = 20
    line_spacing = 10
    
    lines = subtitle.split('\n')
    draw_temp = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    
    line_heights = []
    max_width = 0
    for line in lines:
        bbox = draw_temp.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        line_height = bbox[3] - bbox[1]
        line_heights.append(line_height)
        max_width = max(max_width, line_width)
    
    total_text_height = sum(line_heights) + line_spacing * (len(lines) - 1)
    
    cell_height = img.height + total_text_height + padding * 2
    cell_width = max(img.width, max_width + padding * 2)
    
    cell_img = Image.new('RGBA', (cell_width, cell_height), (0, 0, 0, 0))
    
    x_offset = (cell_width - img.width) // 2
    cell_img.paste(img, (x_offset, 0), img if img.mode == 'RGBA' else None)
    
    draw = ImageDraw.Draw(cell_img)
    
    text_y = img.height + padding
    
    current_y = text_y
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        text_x = (cell_width - line_width) // 2
        
        stroke_width = 3
        draw.text((text_x, current_y), line, font=font, fill=text_color, 
                  stroke_width=stroke_width, stroke_fill=stroke_color)
        
        current_y += line_heights[i] + line_spacing
    
    return cell_img


def create_composite_image(ducks_config, ducks_dir, font, text_color, stroke_color, 
                          images_per_row=5, cell_spacing=20):
    cells = []
    for duck in ducks_config:
        image_path = os.path.join(ducks_dir, duck['file'])
        
        if not os.path.exists(image_path):
            print(f"Warning: Image not found: {image_path}")
            continue
        
        cell = create_duck_cell(image_path, duck['name'], font, text_color, stroke_color)
        cells.append(cell)
    
    if not cells:
        print("Error: No valid images found!")
        return None
    
    num_cells = len(cells)
    num_rows = math.ceil(num_cells / images_per_row)
    
    max_cell_width = max(cell.width for cell in cells)
    max_cell_height = max(cell.height for cell in cells)
    
    composite_width = (max_cell_width * images_per_row) + (cell_spacing * (images_per_row + 1))
    composite_height = (max_cell_height * num_rows) + (cell_spacing * (num_rows + 1))
    
    composite = Image.new('RGBA', (composite_width, composite_height), (0, 0, 0, 0))
    
    for idx, cell in enumerate(cells):
        row = idx // images_per_row
        col = idx % images_per_row
        
        images_in_current_row = min(images_per_row, num_cells - (row * images_per_row))
        
        if images_in_current_row < images_per_row:
            empty_cells = images_per_row - images_in_current_row
            row_offset = (empty_cells * (max_cell_width + cell_spacing)) // 2
        else:
            row_offset = 0
        
        x = row_offset + cell_spacing + (col * (max_cell_width + cell_spacing)) + (max_cell_width - cell.width) // 2
        y = cell_spacing + (row * (max_cell_height + cell_spacing)) + (max_cell_height - cell.height) // 2
        
        composite.paste(cell, (x, y), cell)
    
    return composite


def main():
    ducks_dir = 'ducks'
    yaml_file = 'ducks/ducks.yaml'
    fonts_dir = 'fonts'
    output_dir = 'ducks/output'
    
    ubuntu_font_names = ['Ubuntu-Regular.ttf', 'Ubuntu-R.ttf', 'Ubuntu.ttf']
    font_path = None
    
    for font_name in ubuntu_font_names:
        test_path = os.path.join(fonts_dir, font_name)
        if os.path.exists(test_path):
            font_path = test_path
            break
    
    if font_path is None:
        print(f"Warning: Ubuntu font not found in {fonts_dir}. Checking for any .ttf files...")
        for file in os.listdir(fonts_dir):
            if file.endswith('.ttf'):
                font_path = os.path.join(fonts_dir, file)
                print(f"Using font: {font_path}")
                break
    
    if font_path is None:
        print("Error: No font file found!")
        return
    
    font_size = 40
    try:
        font = ImageFont.truetype(font_path, font_size)
    except Exception as e:
        print(f"Warning: Could not load font {font_path}: {e}")
        font = ImageFont.load_default()
    
    Path(output_dir).mkdir(exist_ok=True)
    
    with open(yaml_file, 'r') as f:
        config = yaml.safe_load(f)
    
    ducks_config = config['ducks']
    
    light_scheme = {
        'text_color': '#11111b',
        'stroke_color': '#cdd6f4'
    }
    
    dark_scheme = {
        'text_color': '#cdd6f4',
        'stroke_color': '#11111b'
    }
    
    print("Creating light version...")
    light_composite = create_composite_image(
        ducks_config, ducks_dir, font, 
        light_scheme['text_color'], light_scheme['stroke_color']
    )
    
    if light_composite:
        light_output = os.path.join(output_dir, 'ducks-light.png')
        light_composite.save(light_output, 'PNG')
        print(f"Created: {light_output}")
    
    print("Creating dark version...")
    dark_composite = create_composite_image(
        ducks_config, ducks_dir, font,
        dark_scheme['text_color'], dark_scheme['stroke_color']
    )
    
    if dark_composite:
        dark_output = os.path.join(output_dir, 'ducks-dark.png')
        dark_composite.save(dark_output, 'PNG')
        print(f"Created: {dark_output}")
    
    print("\nComposite images generated successfully!")


if __name__ == '__main__':
    main()