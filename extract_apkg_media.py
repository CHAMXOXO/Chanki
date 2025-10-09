import os
import re
import shutil
import subprocess
import sys
import zipfile
import json
from pathlib import Path
from PIL import Image

# --- Configuration ---
# 1. Directory to search for .apkg files (e.g., your Downloads folder)
apkg_search_dir = Path("/home/cindy/Downloads")

# 2. Output directory for processed files
processed_output_base_dir = Path("/home/cindy/Med Images/CORDOVA")

# 3. Anki's collection.media folder path
anki_media_dir = Path("/home/cindy/.local/share/Anki2/User 1/collection.media")

# 4. Path to the CairoSVG executable (if you prefer CairoSVG over Inkscape)
cairosvg_path = "" # e.g., "/usr/bin/cairosvg" - leave empty to use Inkscape

# 5. Image conversion settings
target_png_width = 800

# --- End Configuration ---

def run_command(command, error_message):
    """Executes a shell command and raises an error on failure."""
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: {error_message}")
        print(f"Command: {' '.join(command)}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: Command '{command[0]}' not found. Is it installed and in your PATH?")
        sys.exit(1)

def composite_images(base_image_path, overlay_png_path, output_path):
    """Composite base image with overlay mask to create final image."""
    try:
        # Open base image
        base = Image.open(base_image_path).convert('RGBA')
        
        # Open overlay (already converted to PNG)
        overlay = Image.open(overlay_png_path).convert('RGBA')
        
        # Resize overlay to match base image size
        if overlay.size != base.size:
            overlay = overlay.resize(base.size, Image.Resampling.LANCZOS)
        
        # Composite images (overlay on top of base)
        composite = Image.alpha_composite(base, overlay)
        
        # Convert to RGB for JPEG/PNG saving (if output is JPEG)
        if output_path.suffix.lower() in ['.jpg', '.jpeg']:
            composite = composite.convert('RGB')
        
        # Save composite image
        composite.save(output_path, quality=95)
        
        return True
    except Exception as e:
        print(f"  ❌ Image composition failed: {e}")
        return False

def convert_svg_to_png(svg_path, png_path, width=None):
    """Converts an SVG file to PNG using Inkscape or CairoSVG."""
    if cairosvg_path:
        command = [cairosvg_path, str(svg_path), "-o", str(png_path)]
        if width:
            print(f"Warning: target_png_width is not directly supported by CairoSVG without SVG parsing. Using default scale for {svg_path}.")
    else:
        command = ["inkscape", str(svg_path), "--export-filename", str(png_path)]
        if width:
            command.extend(["--export-width", str(width)])
        
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"SVG conversion failed for {svg_path} to {png_path}:")
        print(f"  Command: {' '.join(command)}")
        print(f"  Stdout: {e.stdout}")
        print(f"  Stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"Error: SVG converter not found. Please ensure 'inkscape' (or '{cairosvg_path}' if specified) is installed and in your PATH.")
        return False

def extract_apkg(apkg_path, extract_to_dir):
    """Extracts contents of an .apkg file to a specified directory."""
    print(f"Extracting {apkg_path.name} to {extract_to_dir}...")
    try:
        with zipfile.ZipFile(apkg_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to_dir)
        print("Extraction complete.")
        return True
    except FileNotFoundError:
        print(f"Error: .apkg file not found at {apkg_path}")
        return False
    except zipfile.BadZipFile:
        print(f"Error: Not a valid .zip file (or corrupt) at {apkg_path}")
        return False
    except Exception as e:
        print(f"An error occurred during .apkg extraction: {e}")
        return False

def parse_media_json(media_file_path):
    """Parse the media JSON file to map numbered files to actual filenames."""
    try:
        with open(media_file_path, 'r', encoding='utf-8') as f:
            media_map = json.load(f)
        return media_map
    except FileNotFoundError:
        print(f"Warning: media file not found at {media_file_path}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error: Could not parse media file: {e}")
        return {}

# --- Interactive .apkg selection ---
print(f"\n{'='*60}")
print("SEARCHING FOR .APKG FILES")
print(f"{'='*60}")
print(f"Search directory: {apkg_search_dir}\n")

apkg_files = sorted(list(apkg_search_dir.glob("*.apkg")))

if not apkg_files:
    print(f"❌ Error: No .apkg files found in '{apkg_search_dir}'.")
    print("Please ensure your .apkg files are in the Downloads folder.")
    sys.exit(1)

selected_apkg_paths = []
if len(apkg_files) == 1:
    selected_apkg_paths.append(apkg_files[0])
    print(f"✓ Found 1 .apkg file: '{selected_apkg_paths[0].name}'")
    print(f"  Proceeding with this file.\n")
else:
    print(f"Found {len(apkg_files)} .apkg files:\n")
    for i, apkg_file in enumerate(apkg_files):
        print(f"  [{i+1}] {apkg_file.name}")
    print()
    
    while True:
        choice = input(f"Enter the numbers of the .apkg files to process, separated by commas (e.g., 1,3,5), or 'all' for all files: ").lower()
        if choice == 'all':
            selected_apkg_paths = apkg_files
            print(f"\n✓ Selected all {len(apkg_files)} files.\n")
            break
        else:
            try:
                indices = [int(x.strip()) - 1 for x in choice.split(',')]
                for index in indices:
                    if 0 <= index < len(apkg_files):
                        selected_apkg_paths.append(apkg_files[index])
                    else:
                        print(f"Invalid choice: {index+1}. Skipping.")
                if selected_apkg_paths:
                    print(f"\n✓ Selected {len(selected_apkg_paths)} files.\n")
                    for p in selected_apkg_paths:
                        print(f"  - {p.name}")
                    break
                else:
                    print("No valid files selected. Please try again.")
            except ValueError:
                print("Invalid input. Please enter numbers separated by commas, or 'all'.")

# Ensure base output directory for processed files exists
processed_output_base_dir.mkdir(parents=True, exist_ok=True)


for selected_apkg_path in selected_apkg_paths:
    deck_name = selected_apkg_path.stem
    output_dir_for_deck = processed_output_base_dir / deck_name

    # --- Interactive output directory overwrite prompt (per deck) ---
    if output_dir_for_deck.exists():
        print(f"\n{'='*60}")
        print("OUTPUT DIRECTORY EXISTS")
        print(f"{'='*60}")
        print(f"Directory: {output_dir_for_deck}")
        response = input(f"\nThis directory already exists. Overwrite? (y/N) for {deck_name}: ").lower()
        if response == 'y':
            print(f"✓ Overwriting '{output_dir_for_deck}'...\n")
            shutil.rmtree(output_dir_for_deck)
        else:
            print(f"\n❌ Skipping deck '{deck_name}' to prevent data loss.")
            continue # Skip to the next .apkg file

    output_dir_for_deck.mkdir(parents=True, exist_ok=True)

    # --- Main Script Logic for each deck ---
    temp_extract_dir = output_dir_for_deck / "extracted_apkg_raw"
    temp_extract_dir.mkdir(parents=True, exist_ok=True)

    if not extract_apkg(selected_apkg_path, temp_extract_dir):
        # Clean up temp dir if extraction failed before continuing to next deck
        if temp_extract_dir.exists():
            shutil.rmtree(temp_extract_dir)
        continue # Skip to the next .apkg file

    print(f"\n{'='*60}")
    print(f"PROCESSING DECK: {deck_name}")
    print(f"{'='*60}\n")

    # Parse the media mapping file
    media_file = temp_extract_dir / "media"
    media_map = parse_media_json(media_file)

    if not media_map:
        print("⚠️  Warning: No media mapping found or media file is empty.")
        print("   This might not be a valid image occlusion deck.\n")

    print(f"{'='*60}")
    print(f"MEDIA FILES FOUND: {len(media_map)}")
    print(f"{'='*60}")

    # Display media mapping for debugging
    for num, filename in sorted(media_map.items(), key=lambda x: int(x[0])):
        print(f"  {num:>3} → {filename}")

    print(f"{'='*60}\n")

    # Categorize files
    base_images = []  # .jpg, .png, .gif (non-SVG base images)
    question_svgs = []
    answer_svgs = []
    original_svgs = []
    other_files = []

    # Process media files using the mapping
    for num, filename in media_map.items():
        numbered_file = temp_extract_dir / num
        
        if not numbered_file.exists():
            print(f"⚠️  Warning: File {num} ({filename}) not found in extracted files.")
            continue
        
        file_lower = filename.lower()
        file_ext = Path(filename).suffix.lower()
        
        # Create properly named file in temp directory
        proper_named_file = temp_extract_dir / filename
        if not proper_named_file.exists():
            shutil.copy2(numbered_file, proper_named_file)
        
        if file_ext in [".jpg", ".jpeg", ".png", ".gif"]:
            base_images.append((proper_named_file, filename))
            print(f"📷 BASE IMAGE: {filename}")
        elif file_ext == ".svg":
            if "ques" in file_lower:
                question_svgs.append((proper_named_file, filename))
                print(f"❓ QUESTION MASK: {filename}")
            elif "ans" in file_lower:
                answer_svgs.append((proper_named_file, filename))
                print(f"✅ ANSWER MASK: {filename}")
            elif "orig" in file_lower:
                original_svgs.append((proper_named_file, filename))
                print(f"📄 ORIGINAL SVG: {filename}")
            else:
                other_files.append((proper_named_file, filename))
                print(f"❔ OTHER FILE: {filename}")
        else:
            other_files.append((proper_named_file, filename))
            print(f"📄 OTHER FILE: {filename}")

    print(f"\n{'='*60}")
    print("PROCESSING IMAGES")
    print(f"{'='*60}\n")

    generated_image_paths = []
    
    # Track composite Q&A paths specifically for the Joplin file
    joplin_question_image_filename = None
    joplin_answer_image_filename = None

    files_to_copy_to_anki = []
    
    # First, identify the base image
    base_image_path = None
    if base_images:
        base_image_path = base_images[0][0]  # Get the first base image file path
        original_base_name = base_images[0][1]
        
        # Copy base image to output directory
        dest_path_in_output = output_dir_for_deck / original_base_name
        try:
            shutil.copy2(base_image_path, dest_path_in_output)
            print(f"  ✓ Copied base image: {original_base_name}")
            generated_image_paths.append(dest_path_in_output) # Add to comprehensive list
        except Exception as e:
            print(f"  ❌ Failed to copy base image {original_base_name}: {e}")

    # Process question SVGs and composite with base image
    if question_svgs and base_image_path:
        for file_path, original_name in question_svgs:
            # First convert SVG to PNG
            png_filename = Path(original_name).stem + "_overlay.png"
            png_temp_path = output_dir_for_deck / png_filename
            
            print(f"  Converting QUESTION SVG: {original_name} → {png_filename}")
            if convert_svg_to_png(file_path, png_temp_path, target_png_width):
                # Now composite with base image
                composite_filename = Path(original_name).stem + "_composite.png"
                composite_question_path = output_dir_for_deck / composite_filename
                
                print(f"  Compositing question image: {composite_filename}")
                if composite_images(base_image_path, png_temp_path, composite_question_path):
                    files_to_copy_to_anki.append(composite_question_path)
                    generated_image_paths.append(composite_question_path) # Add to comprehensive list
                    joplin_question_image_filename = composite_question_path.name # Store for Joplin file
                    print(f"    ✓ Question composite created successfully")
                    
                    # Clean up temporary overlay PNG
                    png_temp_path.unlink()
                else:
                    print(f"    ❌ Composition failed, keeping separate files")
                    files_to_copy_to_anki.append(png_temp_path)
                    generated_image_paths.append(png_temp_path) # Add if not composited
            else:
                print(f"    ❌ Conversion failed")

    # Process answer SVGs and composite with base image
    if answer_svgs and base_image_path:
        for file_path, original_name in answer_svgs:
            # First convert SVG to PNG
            png_filename = Path(original_name).stem + "_overlay.png"
            png_temp_path = output_dir_for_deck / png_filename
            
            print(f"  Converting ANSWER SVG: {original_name} → {png_filename}")
            if convert_svg_to_png(file_path, png_temp_path, target_png_width):
                # Now composite with base image
                composite_filename = Path(original_name).stem + "_composite.png"
                composite_answer_path = output_dir_for_deck / composite_filename
                
                print(f"  Compositing answer image: {composite_filename}")
                if composite_images(base_image_path, png_temp_path, composite_answer_path):
                    files_to_copy_to_anki.append(composite_answer_path)
                    generated_image_paths.append(composite_answer_path) # Add to comprehensive list
                    joplin_answer_image_filename = composite_answer_path.name # Store for Joplin file
                    print(f"    ✓ Answer composite created successfully")
                    
                    # Clean up temporary overlay PNG
                    png_temp_path.unlink()
                else:
                    print(f"    ❌ Composition failed, keeping separate files")
                    files_to_copy_to_anki.append(png_temp_path)
                    generated_image_paths.append(png_temp_path) # Add if not composited
            else:
                print(f"    ❌ Conversion failed")

    # Process original SVGs (if needed for reference)
    for file_path, original_name in original_svgs:
        png_filename = Path(original_name).stem + ".png"
        png_output_path = output_dir_for_deck / png_filename
        
        print(f"  Converting ORIGINAL SVG: {original_name} → {png_filename}")
        if convert_svg_to_png(file_path, png_output_path, target_png_width):
            files_to_copy_to_anki.append(png_output_path)
            generated_image_paths.append(png_output_path) # Add to comprehensive list
            print(f"    ✓ Converted successfully")
        else:
            print(f"    ❌ Conversion failed")

    # --- Copy to Anki media folder ---
    print(f"\n{'='*60}")
    print("COPYING TO ANKI MEDIA FOLDER")
    print(f"{'='*60}")
    print(f"Destination: {anki_media_dir}\n")

    copied_to_anki = []
    failed_copies = []

    if anki_media_dir:
        anki_media_dir.mkdir(parents=True, exist_ok=True)
        for src_path in files_to_copy_to_anki:
            try:
                dest_path = anki_media_dir / src_path.name
                shutil.copy2(src_path, dest_path)
                copied_to_anki.append(src_path.name)
                print(f"  ✓ {src_path.name}")
            except Exception as e:
                failed_copies.append((src_path.name, str(e)))
                print(f"  ❌ {src_path.name}: {e}")

    # Clean up temporary extracted .apkg raw files
    if temp_extract_dir.exists():
        print(f"\n  🧹 Cleaning up temporary files: {temp_extract_dir}")
        shutil.rmtree(temp_extract_dir)

    # --- Create comprehensive image paths file for the current deck ---
    image_paths_file_for_deck = output_dir_for_deck / "_image_paths.txt"
    
    print(f"\n{'='*60}")
    print(f"GENERATING ALL IMAGE PATHS FILE FOR DECK: {deck_name}")
    print(f"{'='*60}\n")

    with open(image_paths_file_for_deck, "w", encoding="utf-8") as f:
        f.write(f"--- Successfully Generated Image Paths for Anki Deck: {deck_name} ---\n\n")
        
        if not generated_image_paths:
            f.write("No images were successfully generated for this deck.\n")
        else:
            f.write("The following image filenames (relative to your Anki media folder) were generated and copied:\n\n")
            for img_path in generated_image_paths:
                f.write(f"- {img_path.name}\n")
        
        f.write("\nThese paths can be used directly in your Anki notes or other applications.\n")

    print(f"✓ All image paths saved to: {image_paths_file_for_deck}")

    # --- Create Joplin Q&A specific image paths file for the current deck ---
    if joplin_question_image_filename and joplin_answer_image_filename:
        joplin_qa_paths_file_for_deck = output_dir_for_deck / "_joplin_qa_paths.txt"

        print(f"\n{'='*60}")
        print(f"GENERATING JOPLIN Q&A IMAGE PATHS FILE FOR DECK: {deck_name}")
        print(f"{'='*60}\n")

        with open(joplin_qa_paths_file_for_deck, "w", encoding="utf-8") as f:
            f.write(f"--- Joplin Q&A Image Paths for Anki Deck: {deck_name} ---\n\n")
            f.write("Use these paths for Image Occlusion (Question/Answer) in Joplin:\n\n")
            f.write(f"Question Image: {joplin_question_image_filename}\n")
            f.write(f"Answer Image:   {joplin_answer_image_filename}\n")
            f.write("\nExample usage in Joplin HTML (assuming images are linked or in same note):\n")
            f.write("<span class=\"jta\">\n")
            f.write("  <span class=\"question\">\n")
            f.write(f"    <img src='{joplin_question_image_filename}' data-jta-image-type='question'>\n")
            f.write("    <div class=\"image-question\">Your question text here?</div>\n")
            f.write("  </span>\n")
            f.write("  <details class=\"answer\">\n")
            f.write("    <summary>Show Answer</summary>\n")
            f.write("    <div class=\"answer-text\">\n")
            f.write(f"      <img src='{joplin_answer_image_filename}' data-jta-image-type='answer'>\n")
            f.write("      <p>Your answer text here.</p>\n")
            f.write("    </div>\n")
            f.write("  </details>\n")
            f.write("</span>\n")

        print(f"✓ Joplin Q&A image paths saved to: {joplin_qa_paths_file_for_deck}")

        # --- Auto-open the Joplin Q&A reference file for the current deck ---
        try:
            if joplin_qa_paths_file_for_deck.exists():
                print(f"\nAttempting to open '{joplin_qa_paths_file_for_deck.name}' in gedit...")
                subprocess.Popen(["gedit", str(joplin_qa_paths_file_for_deck)])
        except FileNotFoundError:
            print(f"Warning: 'gedit' command not found. Please open '{joplin_qa_paths_file_for_deck}' manually.")
        except Exception as e:
            print(f"Error opening '{joplin_qa_paths_file_for_deck}': {e}")
    else:
        print(f"\nSkipping Joplin Q&A paths file for '{deck_name}' as either question or answer composite image was not successfully generated.")

    print(f"\n{'='*60}")
    print(f"✅ DECK PROCESSING COMPLETE: {deck_name}")
    print(f"{'='*60}\n")


print(f"\n{'='*60}")
print("✅ ALL SELECTED DECK PROCESSING COMPLETE!")
print(f"{'='*60}\n")
print("NEXT STEPS:")
print("  For each processed deck, the '_image_paths.txt' file has been generated.")
print("  If applicable, a '_joplin_qa_paths.txt' file with direct image occlusion Q&A paths has also been generated and opened in gedit.")
print("  You can now use the image filenames from these files in your Anki notes or Joplin.\n")
print(f"{'='*60}\n")
