FROM python:3.8.12
USER root
ADD . /usr/local/source
# Install necessary packages
RUN pip3 Install -r requirements.txt
# Run the python script
CMD ["python3", "data_preprocessor.py"]