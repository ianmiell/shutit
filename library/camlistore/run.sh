# Example for running
docker run -t -i -p 3179:3179 -v /camlistore:/camlistore -e HOME:/camlistore -e USER:camlistore camlistore  ./bin/camlistored
