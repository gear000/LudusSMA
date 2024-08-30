#!/bin/sh

# List of folder names as a space-separated string
folders="utils"

# Function to create zip files
create_zip() {
    echo "Creating zip file for $folder"
    folder=$1
    mkdir -p "python"
    zip_name="${folder}.zip"
    cp -r "$folder" "python"
    echo "checking if ./python/$folder exists"
    ls -la ./python
    
    if [ -d "$folder" ]; then
        zip -r "$zip_name" "./python/$folder"
        echo "Created $zip_name for the $folder"
    else
        echo "The $folder does not exist"
    fi

    rm -rf "python"
}

# Iterate over each folder in the list and create a zip file
for folder in $folders; do
    create_zip "$folder"
done
