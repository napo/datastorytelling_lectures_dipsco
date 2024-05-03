import pandas as pd
import xml.etree.ElementTree as ET
import base64
import re
import requests
import os

def get_element_by_tag(element, tag):
    """Retrieve an element by tag name, considering namespace."""
    return element.find(f".//{{*}}{tag}")

def decode_field_name(encoded_name):
    """Decode a base64 encoded string."""
    decoded_bytes = base64.b64decode(encoded_name)
    return decoded_bytes.decode('utf-8')

def extract_corrected_data(placemark, category):
    """Extract and return data from a Placemark element with corrected field names and data mapping."""
    data = {}
    extended_data = get_element_by_tag(placemark, 'ExtendedData')
    if extended_data:
        for data_field in extended_data.findall('.//{*}SimpleData'):
            decoded_field_name = decode_field_name(data_field.attrib['name'].split(':')[-1])
            data[decoded_field_name] = data_field.text
    point = get_element_by_tag(placemark, 'Point')
    if point:
        coords = get_element_by_tag(point, 'coordinates').text.split(',')
        data['LONGITUDINE'] = coords[0]
        data['LATITUDINE'] = coords[1]
    data['CATEGORIA'] = category

    # Aggiungi il campo URLIMAGE se esiste nel tag Carousel
    carousel = get_element_by_tag(placemark, 'Carousel')
    if carousel:
        image_url = get_element_by_tag(carousel, 'ImageUrl')
        if image_url is not None:
            data['URLIMAGE'] = image_url.text

    return data

def main():
    file_path = 'lavori_pubblici_trento.kml'
    with open(file_path, 'r') as file:
        kml_content = file.read()
    root = ET.fromstring(kml_content)

    records = []
    for folder in root.findall('.//{*}Folder'):
        category = get_element_by_tag(folder, 'name').text
        for placemark in folder.findall('.//{*}Placemark'):
            record = extract_corrected_data(placemark, category)
            records.append(record)

    df = pd.DataFrame(records)

    # Assicurati che la colonna URLIMAGE esista prima di procedere
    if 'URLIMAGE' in df.columns:
        df['URLIMAGE'] = df['URLIMAGE'].apply(lambda url: url.split('&fife=s')[0] if pd.notna(url) else url)
        for index, url in enumerate(df['URLIMAGE'].dropna()):
            image_name = f'image_{index+1:04d}.jpg'
            response = requests.get(url)
            if response.status_code == 200:
                with open(os.path.join('images', image_name), 'wb') as file:
                    file.write(response.content)
            df.loc[df['URLIMAGE'] == url, 'IMAGENAME'] = image_name

    df.to_csv('output_filename.csv', index=False)

if __name__ == "__main__":
    main()

