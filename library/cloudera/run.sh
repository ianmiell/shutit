# Example for running
docker run -t -i -p 7180:7180 -p 7183:7183 -p 7182:7182 -p 7432:7432 -e JAVA_HOME:/usr/lib/jvm/java-7-oracle-cloudera -e PATH:$JAVA_HOME/bin:$PATH cloudera  
