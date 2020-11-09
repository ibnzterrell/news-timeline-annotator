FROM openjdk:11

LABEL maintainer="Terrell Ibanez <terrell.ibanez@stanford.edu>"

WORKDIR /opt

# Get Stanford CoreNLP
RUN wget http://nlp.stanford.edu/software/stanford-corenlp-latest.zip && \
    unzip stanford-corenlp-latest.zip && \
    rm stanford-corenlp-latest.zip && \
    mv stanford-corenlp-* corenlp

WORKDIR /opt/corenlp

# Get Language Models
RUN wget http://nlp.stanford.edu/software/stanford-corenlp-models-current.jar && \
    wget http://nlp.stanford.edu/software/stanford-english-corenlp-models-current.jar && \
    wget http://nlp.stanford.edu/software/stanford-english-kbp-corenlp-models-current.jar

RUN export CLASSPATH="`find . -name '*.jar'`"

# Run CoreNLP Server on Port 9000
EXPOSE 9000
CMD java -cp "*" -mx4g edu.stanford.nlp.pipeline.StanfordCoreNLPServer