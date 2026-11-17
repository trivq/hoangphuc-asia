FROM odoo:20.0

USER root

# Install any additional system dependencies if needed
# RUN apt-get update && apt-get install -y \
#     libxml2-dev \
#     libxslt1-dev \
#     python3-dev \
#     && rm -rf /var/lib/apt/lists/*

# If you have a requirements.txt, uncomment the following lines
# COPY ./addons/requirements.txt /mnt/extra-addons/requirements.txt
# RUN pip3 install -r /mnt/extra-addons/requirements.txt

USER odoo
