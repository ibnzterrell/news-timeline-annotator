

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
                url: d.web_url
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
const timelineList = d3.select(".timeline").append("ol");

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
                let annotations = events.map(e => {
                    return {
                        note: {
                            title: e.headline,
                            label: `${e.date.toLocaleString('default', { month: 'long' })}, ${e.date.getFullYear()}`
                        },
                        x: xScale(e.date),
                        y: yScale(e.screentime),
                        // TODO Use more accurate placements
                        dx: 30,
                        // Displays below peak if peak is above 75% height of graph
                        dy: (e.screentime > maxScreentime * .75) ? 15 : - 15
                    }
                });

                const makeAnnotations = d3.annotation()
                    //.editMode(true)
                    .type(d3.annotationLabel)
                    .annotations(annotations)

                annotGroup.attr("class", "annotation-group")
                    .call(makeAnnotations);



                timelineList.selectAll('li') // select all list elements 
                    .data(events)  // bind all our event values
                    .join(
                        enter => enter.append('li'), // append an li element for each event
                        update => update,
                        exit => exit.remove()       // remove li elements for removed events
                    )
                    .text(d => `${d.headline}`)
            }
        );
    });


}