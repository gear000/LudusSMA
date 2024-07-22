#!/bin/bash

# List of folder names
folders=("utils")

# Function to create zip files
create_zip() {
    folder=$1
    mkdir -p "python"
    zip_name="${folder}.zip"
    cp -r "$folder" "python"
    
    if [ -d "$folder" ]; then
        zip -r "$zip_name" "./python/$folder"
        echo "Created $zip_name for the $folder"
    else
        echo "The $folder does not exist"
    fi

    rm -rf "python"
}

cd ./lambda_functions

# Iterate on each folder in the list and create a zip file
for folder in "${folders[@]}"; do
    create_zip "$folder"
done
