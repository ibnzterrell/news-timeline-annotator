package edu.stanford.tvnews;

import lombok.Builder;
import lombok.Data;

@Builder
@Data
public class TemporalEvent {
	private String uri;
	private String eventDate;
}
