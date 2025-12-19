import os
import sys
import time
import slicer

# Create log file
log_file = r"D:\Vol to nrrd\conversion_kretz_log.txt"

def log_message(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"[{timestamp}] {message}"
    print(full_message)
    sys.stdout.flush()
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(full_message + "\n")
        f.flush()

def main():
    log_message("=== Kretz VOL to NIFTI Conversion ===")
    
    input_folder = r"D:\Vol to nrrd\USVolume"
    output_folder = r"D:\Vol to nrrd\Nifti_files"  # Changed folder name to Nifti_files
    
    log_message(f"Input folder: {input_folder}")
    log_message(f"Output folder: {output_folder}")
    
    # Check if Kretz file reader is available
    try:
        # Look for Kretz file reader in available modules
        module_names = [name for name in dir(slicer.modules) if not name.startswith('_')]
        kretz_modules = [name for name in module_names if 'kretz' in name.lower()]
        
        log_message(f"Available Kretz-related modules: {kretz_modules}")
        
        if kretz_modules:
            log_message("✅ Kretz file reader modules found")
        else:
            log_message("❌ No Kretz file reader modules found")
            log_message("Available modules: " + ", ".join(module_names))
            
    except Exception as e:
        log_message(f"Error checking modules: {e}")
    
    # Check input folder
    if not os.path.exists(input_folder):
        log_message("❌ Input folder does not exist")
        return False
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        log_message("✅ Created output folder")
    
    # Get VOL files
    try:
        files = os.listdir(input_folder)
        vol_files = [f for f in files if f.lower().endswith('.vol')]
        log_message(f"Found {len(vol_files)} VOL files: {vol_files}")
    except Exception as e:
        log_message(f"❌ Error reading input folder: {e}")
        return False
    
    if not vol_files:
        log_message("No VOL files found")
        return False
    
    success_count = 0
    
    for filename in vol_files:
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename.replace('.vol', '.nii'))  # Changed to .nii
        
        log_message(f"\n--- Processing: {filename} ---")
        log_message(f"Input: {input_path}")
        log_message(f"Output: {output_path}")
        
        try:
            # Check file exists
            if not os.path.exists(input_path):
                log_message("❌ File does not exist")
                continue
            
            file_size = os.path.getsize(input_path)
            log_message(f"File size: {file_size} bytes")
            
            # Method 1: Try loading with specific properties for Kretz files
            log_message("Attempting to load Kretz VOL file...")
            
            # Use the file reader that supports Kretz format
            properties = {
                'fileName': input_path,
                'name': os.path.splitext(filename)[0],
                'scanConvert': True,  # Convert from polar to Cartesian coordinates
                'outputSpacing': 0.5  # Output spacing in mm
            }
            
            volumeNode = slicer.util.loadNodeFromFile(input_path, "KretzFile", properties)
            
            if volumeNode is None:
                log_message("❌ Kretz-specific loading failed, trying generic...")
                # Fallback to generic loading
                volumeNode = slicer.util.loadVolume(input_path)
            
            if volumeNode is None:
                log_message("❌ All loading methods failed")
                continue
            
            log_message(f"✅ Successfully loaded: {volumeNode.GetName()}")
            log_message(f"Node class: {volumeNode.GetClassName()}")
            
            # Check image data
            if not volumeNode.GetImageData():
                log_message("❌ No image data in loaded volume")
                slicer.mrmlScene.RemoveNode(volumeNode)
                continue
            
            dimensions = volumeNode.GetImageData().GetDimensions()
            log_message(f"Image dimensions: {dimensions}")
            
            # Get more volume information
            if volumeNode.IsA('vtkMRMLScalarVolumeNode'):
                displayNode = volumeNode.GetDisplayNode()
                if displayNode:
                    log_message(f"Window/Level: {displayNode.GetWindow()}/{displayNode.GetLevel()}")
            
            # Save as NIFTI (instead of NRRD)
            log_message("Saving as NIFTI...")
            success = slicer.util.saveNode(volumeNode, output_path, {"fileType": "NIFTI"})
            log_message(f"Save function returned: {success}")
            
            if success and os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                log_message(f"✅ SUCCESS: Saved {file_size} bytes")
                success_count += 1
            else:
                log_message("❌ Save failed or file not created")
                if os.path.exists(os.path.dirname(output_path)):
                    log_message(f"Output folder exists: {os.path.exists(os.path.dirname(output_path))}")
                else:
                    log_message("Output folder does not exist")
            
            # Clean up
            slicer.mrmlScene.RemoveNode(volumeNode)
            log_message("Cleaned up volume node")
            
        except Exception as e:
            log_message(f"❌ Error: {str(e)}")
            import traceback
            log_message(f"Traceback: {traceback.format_exc()}")
    
    log_message(f"\n=== Conversion Summary ===")
    log_message(f"Successfully converted: {success_count}/{len(vol_files)} files")
    
    if success_count > 0:
        log_message("🎉 Conversion successful!")
        try:
            output_files = os.listdir(output_folder)
            nifti_files = [f for f in output_files if f.lower().endswith(('.nii', '.nii.gz'))]  
            log_message(f"Created files: {nifti_files}")
        except Exception as e:
            log_message(f"Could not list output: {e}")
    else:
        log_message("💥 Conversion failed")
    
    return success_count > 0

if __name__ == "__main__":
    # Initialize log
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"=== Kretz conversion started at {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
    
    try:
        log_message("Script starting...")
        success = main()
        log_message(f"Script completed: {success}")
    except Exception as e:
        log_message(f"💥 Fatal error: {str(e)}")
        import traceback
        log_message(traceback.format_exc())
    
    log_message("=== Script finished ===")
