package edu.stanford.tvnews;

import java.util.List;
import java.util.Properties;

import edu.stanford.nlp.ling.CoreAnnotations;
import edu.stanford.nlp.pipeline.Annotation;
import edu.stanford.nlp.pipeline.AnnotationPipeline;
import edu.stanford.nlp.pipeline.POSTaggerAnnotator;
import edu.stanford.nlp.pipeline.TokenizerAnnotator;
import edu.stanford.nlp.pipeline.WordsToSentencesAnnotator;
import edu.stanford.nlp.time.TimeAnnotations;
import edu.stanford.nlp.time.TimeAnnotator;
import edu.stanford.nlp.time.TimeExpression;
import edu.stanford.nlp.util.CoreMap;

public class TemporalPipeline {
    private Properties props = new Properties();
    private AnnotationPipeline pipeline = new AnnotationPipeline();

    public TemporalPipeline() {
        pipeline.addAnnotator(new TokenizerAnnotator(false));
        pipeline.addAnnotator(new WordsToSentencesAnnotator(false));
        pipeline.addAnnotator(new POSTaggerAnnotator(false));
        pipeline.addAnnotator(new TimeAnnotator("sutime", props));
    }

    private Annotation annotate(String docDate, String text) {
        Annotation annotation = new Annotation(text);
        annotation.set(CoreAnnotations.DocDateAnnotation.class, docDate);
        pipeline.annotate(annotation);
        return annotation;
    }

    public TemporalEvent temporalizeEvent(TemporalDocument document) {
        Annotation markedDocument = annotate(document.getPublishDate(), document.getText());

        // Use document publish date if No Date is Mentioned
        String eventDate = document.getPublishDate();

        List<CoreMap> timexAnnotations = markedDocument.get(TimeAnnotations.TimexAnnotations.class);

        // Get first date mentioned in text, if there is one
        if (timexAnnotations.size() > 0) {
            // CoreNLP's SUTime sometimes resolves dates in the future
            // HeidelTime was trained on news and performs bettter
            // Conside switching when CoreNLP supports it
            eventDate = timexAnnotations.get(0).get(TimeExpression.Annotation.class).getTemporal().prev().toString();
        }

        return new TemporalEvent.TemporalEventBuilder().uri(document.getUri()).eventDate(eventDate).build();
    }
}