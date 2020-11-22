

const queryRegex = /(.*?)="(.*?)"/;
async function getData(queryText) {
    // TODO: Handle queries other than names
    const queryType = queryText.match(queryRegex)[1]
    switch (queryType) {
        case "name":
            return getPersonData(queryText.match(queryRegex)[2]);
        default:
            return [];
    }
}

async function getPersonData(name) {
    let data = d3.csv(`http://localhost:3000/person/${name}/screentime`,
        (d) => {
            return {
                date: d3.timeParse("%Y-%m-%d")(d.date),
                date_ISO: d.date,
                // Convert seconds to minutes
                screentime: d.screentime / 60
            };
        });
    return data;
}

async function getPersonEvents(name, timedata) {
    let data = d3.csv(`http://localhost:3000/person/${name}/events`,
        (d) => {
            return {
                date: d3.timeParse("%Y-%m")(d.month_date),
                // TODO: Use NLP Event Date instead of publish date
                pub_date: d.pub_date,
                screentime: timedata.find(t => t.date_ISO.substring(0, 7) === d.month_date).screentime,
                headline: d.main_headline,
                snippet: d.snippet,
                section: d.section_name,
                people: d.people,
                organizations: d.organizations,
                topics: d.subjects,
                url: d.web_url,
                uri: d.uri
            };
        });
    return data;
}

const plotVars = ({
    plotWidth: 1120,   // Width of plot region matching Stanford Cable TV News Analyzer
    plotHeight: 400,  // Height of plot region matching Stanford Cable TV News Analyzer
    plotMargin: 50   // Margin space for axes and their labels
});


const svgContainer = d3.select(".graph").append('svg').attr("width", plotVars.plotWidth)
    .attr("height", plotVars.plotHeight)
    .style("background-color", "whitesmoke");

const line = svgContainer.append("path");
const annotGroup = svgContainer.append("g");
const timelineList = d3.select(".timeline");
const localeOptions = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };

function randomBool() {
    return Math.floor(Math.random() * 2) == 1;
}

function annotate(url) {
    // Ignore Empty URLs
    if (url === "") {
        return;
    }
    // Get the query from the URL
    let query = url.replace("https://tvnews.stanford.edu/?dataVersion=v1&data=", "");
    // Base64 Decode
    query = atob(query);
    // Load JSON
    query = JSON.parse(query);
    console.log(query);

    // Get the data for the first query
    getData(query.queries[0].text).then((data) => {
        console.log(data);
        // Set up scales
        let xScale = d3.scaleTime().domain(d3.extent(data, d => d.date)).range([0, plotVars.plotWidth]);
        let yScale = d3.scaleLinear().domain([0, d3.max(data, d => d.screentime)]).range([plotVars.plotHeight, 0]);

        const maxScreentime = d3.max(data, d => d.screentime);

        // Generate and attach line data
        let lineGenerator = d3.line().x(d => xScale(d.date)).y(d => yScale(d.screentime));
        line.datum(data).attr("d", d => lineGenerator(d)).attr("fill", "none").attr("stroke", "firebrick");

        getPersonEvents(query.queries[0].text.match(queryRegex)[2], data).then(
            (events) => {
                console.log(events);
                let annotations = events.map((e, i) => {
                    let ex = xScale(e.date);
                    let ey = yScale(e.screentime);

                    // TODO Proper label placement algo 
                    // Heuristic for label placement for now
                    let xOffset = (i / events.length) * plotVars.plotWidth + 70;
                    // Evenly distribute X placement
                    // Y Stagger based on even / odd index
                    let yOffset = (i % 2 === 1) ? 150 : 300;
                    let edx = -ex + xOffset;
                    let edy = -ey + yOffset;

                    return {
                        note: {
                            title: e.headline,
                            label: `${e.date.toLocaleString('default', { month: 'short' })}, ${e.date.getFullYear()}`,
                        },
                        x: ex,
                        y: ey,
                        dx: edx,
                        dy: edy,
                        connector: { end: "arrow" },

                    }
                });

                const makeAnnotations = d3.annotation()
                    //.editMode(true)
                    .type(d3.annotationLabel)
                    .annotations(annotations)

                annotGroup.attr("class", "annotation-group")
                    .call(makeAnnotations);



                timelineList.selectAll(".event") // select all list elements 
                    .data(events, e => e.uri)  // bind all our event values
                    .join(
                        enter => {
                            let eDiv = enter.append("div");
                            eDiv.attr("class", "event");
                            eDiv.append("h3").text(d => `${d.headline}`);
                            eDiv.append("h4").text(d => `${new Date(d.pub_date).toLocaleDateString("en-us", localeOptions)} - ${d.section}`);
                            eDiv.append("p").text(d => `${d.snippet}`);
                            eDiv.append("p").text(d => `People: ${d.people}`);
                            eDiv.append("p").text(d => `Organizations: ${d.organizations}`);
                            eDiv.append("p").text(d => `Topics: ${d.topics}`);
                            eDiv.append("a").attr("href", d => `${d.url}`).text(d => `${d.url}`);
                            return eDiv;
                        }, // append a div for each event
                        update => update,
                        exit => exit.remove()       // remove divs for removed events
                    )

            }
        );
    });


}