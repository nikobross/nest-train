# Image Display and Coordinate System

## Image Display Size

Images are displayed at **50% of their original size** in the browser for easier viewing and annotation. This is purely a visual scaling - the annotations are stored with accurate coordinates.

## How Coordinates Work

### Display
- Images shown at **50% scale** via CSS (`max-width: 50%`)
- Canvas overlay matches the **displayed** image size
- Drawing boxes works on the visible 50% size

### Storage
- All box coordinates are **normalized** to 0-1 scale
- Stored relative to **original** image dimensions
- Independent of display size

### Example

If an image is 4000x3000 pixels:
- **Displayed:** 2000x1500 pixels (50%)
- **Canvas:** 2000x1500 pixels (matches display)
- **Drawing:** Box at pixels (100, 100) to (300, 200) on canvas
- **Stored:** Normalized coordinates relative to canvas
  - x: 100/2000 = 0.05
  - y: 100/1500 = 0.067
  - width: 200/2000 = 0.10
  - height: 100/1500 = 0.067

### When Loading for ML

To get pixel coordinates on original image:
```python
# From exported JSON
box = annotation['boxes'][0]  # e.g., {x: 0.05, y: 0.067, width: 0.10, height: 0.067}

# Original image dimensions
original_width = 4000
original_height = 3000

# Convert to pixels on original image
x_pixel = box['x'] * original_width      # 0.05 * 4000 = 200
y_pixel = box['y'] * original_height     # 0.067 * 3000 = 200
width_pixel = box['width'] * original_width    # 0.10 * 4000 = 400
height_pixel = box['height'] * original_height # 0.067 * 3000 = 200
```

## Benefits of This Approach

1. **Accurate annotations**: Coordinates always map correctly to original images
2. **Easier viewing**: Large images fit better on screen at 50%
3. **Resolution independent**: Works with any image size
4. **ML compatible**: Normalized coordinates are standard format

## Adjusting Display Size

To change the display size, edit `frontend/css/styles.css`:

```css
#current-image {
    max-width: 50%;  /* Change to 75%, 100%, 33%, etc. */
    height: auto;
    display: block;
}
```

The coordinate system will automatically adjust - no other changes needed!

## Technical Details

The JavaScript automatically:
1. Gets displayed image size using `clientWidth/clientHeight`
2. Sizes canvas to match displayed dimensions
3. Normalizes boxes on save: `pixel_coord / canvas_dimension`
4. Denormalizes on load: `normalized_coord * canvas_dimension`

This ensures annotations are always accurate regardless of display scaling.
