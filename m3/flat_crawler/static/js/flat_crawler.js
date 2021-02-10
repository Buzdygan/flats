// variable that keeps all the filter information

var send_data = {}
const star = "&#9733;";
const empty_star = "&#9734;";


$(document).ready(function () {
    // reset all parameters on page load

    resetFilters();
    // bring all the data without any filters

    getAPIData();

    get_districts();

    // on filtering the district input

    $('#districts').on('change', function () {
        if(this.value == "all")
            send_data['district'] = "";
        else
            send_data['district'] = this.value;
        getAPIData();
    });

    // sort the data according to price/points

    $('#sort_by').on('change', function () {
        send_data['sort_by'] = this.value;
        getAPIData();
    });

    // display the results after reseting the filters

    $("#display_all").click(function(){
        resetFilters();
        getAPIData();
    })
})


/**
    Function that resets all the filters   
**/
function resetFilters() {
    $("#districts").val("all");
    $("#sort_by").val("none");

    get_districts("all");

    send_data['exclude_rejected'] = 'true';
    send_data['district'] = '';
    send_data["sort_by"] = '',
    send_data['format'] = 'json';
}


const rtype_to_color = {
    'heart': 'red',
    'star': 'gold',
    'reject': 'black'
}

function updateFlat(flat_id, rtype, is_ticked) {
    let url = $('#flatlist').attr("url");
    $.ajax({
        method: 'GET',
        url: url,
        data: {
            'flat_id': flat_id,
            'rating_type': rtype,
            'is_ticked': is_ticked,
        },
    });
}

function tickRate(flat_id, rtype, update) {
    var rate_el = document.getElementById(rtype + ':' + flat_id);
    rate_el.setAttribute('data-ticked', 'true');
    rate_el.style.color = rtype_to_color[rtype];
    if (update) {
        updateFlat(flat_id, rtype, "true");
    }
}

function untickRate(flat_id, rtype, update) {
    var rate_el = document.getElementById(rtype + ':' + flat_id);
    rate_el.setAttribute('data-ticked', 'false')
    rate_el.style.color = "grey"
    if (update) {
        updateFlat(flat_id, rtype, "false");
    }
}

function clickRate(flat_id, rtype) {
    console.log(flat_id + ':' + rtype);
    var rate_el = document.getElementById(rtype + ':' + flat_id);

    var ticked = rate_el.getAttribute('data-ticked')
    if(ticked != 'true') {
        tickRate(flat_id, rtype, true);
        ['heart', 'star', 'reject'].forEach(item => {
            if(item != rtype) {
                untickRate(flat_id, item, false);
            }
        })
    } else {
        untickRate(flat_id, rtype, true)
    } 
    getAPIData();
}

function heartFlat(flat_id) {
    clickRate(flat_id, 'heart');
}

function starFlat(flat_id) {
    clickRate(flat_id, 'star');
}

function rejectFlat(flat_id) {
    clickRate(flat_id, 'reject');
}


/**.
    Utility function to showcase the api data 
    we got from backend to the table content
**/
function putTableData(result) {
    // creating table row for each result and

    // pushing to the html cntent of table body of listing table

    let row;
    if(result["results"].length > 0){
        $("#no_results").hide();
        $("#list_data").show();
        $("#flatlist").html("");  
        $.each(result["results"], function (a, b) {
            if (b.rejected) {
                return;
            }
            row = "<div class='flat-post'> " +
                "<div class='thumbnail'><img src='data:image/png;base64," + b.thumbnail_image + "'></div>" +
                "<div class='text'>" +
                    "<div class='title'><a class='post-link' href='" + b.url + "'> " + 
                        b.heading.substring(0, 60) +
                    '</a></div>' + 
                    "<div class='description'>" + b.desc.substring(0, 300) + "</div>" +
                "</div>" +
                "<div class='info'>" +
                    "<span class='price-text'>" + Math.ceil(b.min_price / 1000) + " tys. zł </span>" +
                    "<div class='size'>" + b.size_m2 + " m2</div>" +
                    "<div class='district'>" + b.district + "</div>" + 
                    "<span class='rating'>" +
                        "<span class='heart'>" +
                            "<button class='heart-button' id='heart:" + b.id + "' onclick=heartFlat('" + b.id + "') > &#9829; </button>" + 
                        "</span>" + 
                        "<span class='star'>" +
                            "<button class='star-button' id='star:" + b.id + "' onclick= starFlat('" + b.id + "'); >" + star + "</button>" + 
                        "</span>" + 
                        "<span class='reject'>" +
                            "<button class='reject-button' id='reject:" + b.id + "' onclick=rejectFlat('" + b.id + "') > &#215; </button>" + 
                        "</span>" +
                    "</span>" +
                "</div>"
            "</div>"
            $("#flatlist").append(row);   
            if (b.hearted) {
                tickRate(b.id, 'heart', false);
            } else {
                untickRate(b.id, 'heart', false);
            }

            if (b.starred) {
                tickRate(b.id, 'star', false);
            } else {
                untickRate(b.id, 'star', false);
            }

            if (b.rejected) {
                tickRate(b.id, 'reject', false);
            } else {
                untickRate(b.id, 'reject', false);
            }
        });
        // $.each(result["results"], function (a, b) {
        // });
    }
    else{
        // if no result found for the given filter, then display no result

        $("#no_results h5").html("No results found");
        $("#list_data").hide();
        $("#no_results").show();
    }
    // setting previous and next page url for the given result

    let prev_url = result["previous"];
    let next_url = result["next"];
    // disabling-enabling button depending on existence of next/prev page. 

    if (prev_url === null) {
        $("#previous").addClass("disabled");
        $("#previous").prop('disabled', true);
    } else {
        $("#previous").removeClass("disabled");
        $("#previous").prop('disabled', false);
    }
    if (next_url === null) {
        $("#next").addClass("disabled");
        $("#next").prop('disabled', true);
    } else {
        $("#next").removeClass("disabled");
        $("#next").prop('disabled', false);
    }
    // setting the url

    $("#previous").attr("url", result["previous"]);
    $("#next").attr("url", result["next"]);
    // displaying result count

    $("#result-count span").html(result["count"]);
}

function getAPIData() {
    let url = $('#list_data').attr("url")
    $.ajax({
        method: 'GET',
        url: url,
        data: send_data,
        beforeSend: function(){
            $("#no_results h5").html("Loading data...");
        },
        success: function (result) {
            putTableData(result);
        },
        error: function (response) {
            $("#no_results h5").html("Something went wrong");
            $("#list_data").hide();
        }
    });
}

$("#next").click(function () {
    // load the next page data and 

    // put the result to the table body

    // by making ajax call to next available url

    let url = $(this).attr("url");
    if (!url)
        $(this).prop('all', true);

    $(this).prop('all', false);
    $.ajax({
        method: 'GET',
        url: url,
        success: function (result) {
            putTableData(result);
        },
        error: function(response){
            console.log(response)
        }
    });
})

$("#previous").click(function () {
    // load the previous page data and 

    // put the result to the table body 

    // by making ajax call to previous available url

    let url = $(this).attr("url");
    if (!url)
        $(this).prop('all', true);

    $(this).prop('all', false);
    $.ajax({
        method: 'GET',
        url: url,
        success: function (result) {
            putTableData(result);
        },
        error: function(response){
            console.log(response)
        }
    });
})


function get_districts() {
    // fill the options of provinces by making ajax call

    // obtain the url from the provinces select input attribute

    let url = $("#districts").attr("url");
    // makes request to getProvince(request) method in views

    let district_option = "<option value='all' selected>All Districts</option>";
    $.ajax({
        method: 'GET',
        url: url,
        data: {
        },
        success: function (result) {
            $.each(result["districts"], function (a, b) {
                district_option += "<option>" + b + "</option>"
            });
            $("#districts").html(district_option)
        },
        error: function(response){
            console.log(response)
        }
    });
}
