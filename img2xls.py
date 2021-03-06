#!/usr/bin/python3
"""Convert images to colored cells in an Excel spreadsheet.
"""
import sys
import xlwt
import os
import re
from PIL import Image

def load_image_rgb(path):
    """Ensures the image to be in RGB format."""
    img = Image.open(path)
    return img.convert('RGB')

def prepare_image(img):
    """Scales down if needed"""
    width, height = img.size
    if width > 256 or height > 256:
        fact = 256.0 / max(width, height)
        img = img.resize((int(fact*width), int(fact*height)), Image.BILINEAR)
    return img

def map2d(size, func):
    """Apply function to every point in [(0,0) ... (width-1, height-1)]."""
    width, height = size
    for y_pos in range(height):
        for x_pos in range(width):
            func(x_pos, y_pos)

def get_col_reduced_palette_image(img):
    """Returns image reduced to in Excel allowed number of colors."""
    cust_col_num_range = (8, 64)
    col_cnt = cust_col_num_range[1] - cust_col_num_range[0]
    pal_img = img.convert('P', palette=Image.ADAPTIVE, colors=col_cnt)
    pal_pixels = pal_img.load()
    def add_col_offset(x_pos, y_pos):
        """Add minimum color number to a pixel in palette image."""
        pal_pixels[x_pos, y_pos] += cust_col_num_range[0]
    map2d(pal_img.size, add_col_offset)
    return pal_img

def scale_table_cells(sheet1, img_size, c_size):
    """Adjust cell size to image resolution."""
    width, height = img_size
    c_width, c_height = c_size
    max_edge = max(width, height)
    col_width = int(c_width / max_edge)
    row_height = int(c_height / max_edge)
    for x_pos in range(width):
        sheet1.col(x_pos).width = col_width
    for y_pos in range(height):
        sheet1.row(y_pos).height = row_height

def create_workbook_with_sheet(name):
    """Removes non-alpha-numerical values in name."""
    book = xlwt.Workbook()
    valid_name = re.sub(r'[^\.0-9a-zA-Z]+', '', os.path.basename(name))
    sheet1 = book.add_sheet(valid_name)
    return book, sheet1

def gen_style_lookup(img, pal_img, book):
    """Create lookup dict for accessing spreadsheet styles by image color."""
    img_pixels = img.load()
    pal_pixels = pal_img.load()
    assert img.size == pal_img.size
    already_used_colors = set()
    style_lookup = {}

    def add_style_lookup(x_pos, y_pos):
        """Add a new style to lookup table for one pixel if needed."""
        palcolnum = pal_pixels[x_pos, y_pos]
        if palcolnum in already_used_colors:
            return
        already_used_colors.add(palcolnum)
        col_name = "custom_colour_" + str(palcolnum)
        xlwt.add_palette_colour(col_name, palcolnum)
        book.set_colour_RGB(palcolnum, *img_pixels[x_pos, y_pos])
        style = xlwt.easyxf('pattern: pattern solid, fore_colour ' + col_name)
        style.pattern.pattern_fore_colour = palcolnum
        style_lookup[palcolnum] = style

    map2d(img.size, add_style_lookup)

    return style_lookup

def set_cell_colors(pal_img, style_lookup, sheet):
    """Pixelwise copies colors from image into table."""
    pal_pixels = pal_img.load()
    def write_sheet_cell(x_pos, y_pos):
        """Set a single pixel, i.e. cell, in table."""
        sheet.write(y_pos, x_pos, ' ', style_lookup[pal_pixels[x_pos, y_pos]])
    map2d(pal_img.size, write_sheet_cell)

def img2xls(c_width, img_path, xls_path):
    """Convert image to spreadsheet."""
    img = load_image_rgb(img_path)
    img = prepare_image(img)
    pal_img = get_col_reduced_palette_image(img)

    book, sheet1 = create_workbook_with_sheet(img_path)

    style_lookup = gen_style_lookup(img, pal_img, book)

    set_cell_colors(pal_img, style_lookup, sheet1)

    scale_table_cells(sheet1, img.size, c_width)

    book.save(xls_path)
    print('saved', xls_path)

def print_usage():
    """Show command line usage."""
    print("Usage: python img2xls.py format image")
    print("                         format = libre -> LibreOffice xls")
    print("                         format = ms    -> Microsoft Office xls")
    print("                         format = mac   -> Mac Office xls")

def abort_with_usage():
    """Quit program because of invalid command line usage."""
    print_usage()
    sys.exit(2)

def main():
    """Parse command line and run."""
    if len(sys.argv) != 3:
        abort_with_usage()

    switch = sys.argv[1]

    size_dict = {"libre": (25000, 10000),
                 "ms": (50000, 10000),
                 "mac": (135000, 10000)}

    if not switch in size_dict:
        abort_with_usage()

    img_path = sys.argv[2]
    xls_path = img_path + "." + switch + ".xls"

    img2xls(size_dict[switch], img_path, xls_path)

if __name__ == "__main__":
    sys.exit(main())
