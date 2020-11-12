package edu.stanford.tvnews;

import java.util.HashMap;
import java.util.Map;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.amazonaws.services.lambda.runtime.events.APIGatewayProxyRequestEvent;
import com.amazonaws.services.lambda.runtime.events.APIGatewayProxyResponseEvent;
import com.google.gson.Gson;

public class TemporalServiceHandler
		implements RequestHandler<APIGatewayProxyRequestEvent, APIGatewayProxyResponseEvent> {

	private TemporalPipeline temporalPipeline = new TemporalPipeline();
	private Gson gson = new Gson();

	private APIGatewayProxyResponseEvent createResponse() {
		APIGatewayProxyResponseEvent response = new APIGatewayProxyResponseEvent();
		Map<String, String> headers = new HashMap<>();
		headers.put("Content-Type", "application/json");
		return response;
	}

	private APIGatewayProxyResponseEvent warmup() {
		APIGatewayProxyResponseEvent response = createResponse();
		response.setStatusCode(204);
		return response;
	}

	private APIGatewayProxyResponseEvent temporal(APIGatewayProxyRequestEvent request) {
		APIGatewayProxyResponseEvent response = createResponse();

		TemporalDocument document = gson.fromJson(request.getBody(), TemporalDocument.class);
		TemporalEvent event = temporalPipeline.temporalizeEvent(document);
		response.setBody(gson.toJson(event));
		response.setStatusCode(200);

		return response;
	}

	@Override
	public APIGatewayProxyResponseEvent handleRequest(final APIGatewayProxyRequestEvent request,
			final Context context) {
		APIGatewayProxyResponseEvent response;

		switch (request.getPath()) {
			case "/temporal":
				response = temporal(request);
				break;

			case "/warmup":
				response = warmup();
				break;

			default:
				response = createResponse();
				response.setStatusCode(404);
				break;
		}

		return response;
	}
}
