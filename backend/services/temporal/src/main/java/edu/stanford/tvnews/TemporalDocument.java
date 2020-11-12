package edu.stanford.tvnews;

import lombok.Data;

@Data
public class TemporalDocument {
	private String uri;
	private String publishDate;
	private String text;
}