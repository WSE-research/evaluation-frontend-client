import streamlit as st
from code_editor import code_editor
import requests
import pandas as pd
from decouple import config

BACKEND_URL = config("BACKEND_URL")

st.set_page_config(layout="wide")

evaluation_title = "Composed explanations";
tuple_size = 5;

if "user_id" not in st.session_state:
    st.session_state.user_id = None;
if "number_of_correctness" not in st.session_state:
    st.session_state.number_of_correctness = 0;
if "number_of_understandability" not in st.session_state:
    st.session_state.number_of_understandability = 0;
if "correctness_done" not in st.session_state:
    st.session_state.correctness_done = 0;
if "understandability_done" not in st.session_state:
    st.session_state.understandability_done = 0;
if "current_understandability_index" not in st.session_state:
    st.session_state.current_understandability_index = 0;
if "current_correctness_index" not in st.session_state:
    st.session_state.current_correctness_index = 0;
if "correctness_tuples" not in st.session_state:
    st.session_state.correctness_tuples = None;     
if "understandability_tuples" not in st.session_state:
    st.session_state.understandability_tuples = None;
if "current_metric" not in st.session_state:
    st.session_state.current_metric = "Correctness";
if "best_worst_current" not in st.session_state:
    st.session_state.best_worst_current = {
        "tuple": None,
        "best": None,
        "worst": None
    }
if "experiment_selection" not in st.session_state:
    st.session_state.experiment_selection = 1.0;

if "hash_explanation_dict" not in st.session_state:
    st.session_state.hash_explanation_dict = pd.read_csv("hash_explanation_dict.csv", index_col=0, header=None).to_dict(orient="index");
if "hash_explanation_dict_inputdata" not in st.session_state:
    st.session_state.hash_explanation_dict_inputdata = pd.read_csv("hash_explanation_dict_inputdata.csv", index_col=0, header=None).to_dict(orient="index");   
if "hash_explanation_dict_outputdata" not in st.session_state:
    st.session_state.hash_explanation_dict_outputdata = pd.read_csv("hash_explanation_dict_outputdata.csv", index_col=0, header=None).to_dict(orient="index"); 
if "all_correctness_experiments" not in st.session_state:
    st.session_state.all_correctness_experiments = None;
if "metadata_dict" not in st.session_state:
    st.session_state.metadata_dict = pd.read_csv("hash_explanation_metadata_dict.csv", header=None, names=['Hash','metadata'], index_col=0).to_dict(orient="index");

st.title(f"{evaluation_title} evaluation");
st.header(f"Current evaluated metric: {st.session_state.current_metric}");
if st.session_state.current_metric == "Understandability":
    st.subheader("Select only one explanation as best and one as worst!")
    st.text("You can change your decision at any time, the latest selections will be stored");
    st.text("""From your personal point of view, select the best and the least comprehensible explanation. Do not consider correctness, as this will be assessed separately.
Concentrate on things like readability, helpfulness, length and/or details. Please select only one explanation as "Best" and another as "Worst".""")

elif st.session_state.current_metric == "Correctness":
    st.text("You can change your decision at any time, the latest selections will be stored");
    st.text("""As an expert, you should consider the input (SPARQL queries) and output data (RDF triples) and calculate how many errors occur in the delivered explanation.
            An error-free statement therefore contains 0 errors. An error is any statement that is incorrectly derived from the data, e.g. 
1) Input data: Any variable is selected, although only `?s` is asked for
2) Output data: Mention of `annotationId` with incorrect timestamp

Please indicate the cumulative errors for explanation and go to the next or previous experiment. In both cases, the value will be saved.""")

st.divider();
selection = st.empty();

############## METHODS ##############

def switch_metric():
    if(st.session_state.current_metric == "Correctness"):
        st.session_state.current_metric = "Understandability";
    elif(st.session_state.current_metric == "Understandability"):
        st.session_state.current_metric = "Correctness";

def setup_u_experiments(dict):
    experiments_tuples = [];
    for (key,val) in dict.items():
        experiments_tuples.append({
            "tuple": key,
            "best": val["best"],
            "worst": val["worst"]
        });
    st.session_state.understandability_tuples = experiments_tuples;

def setup_c_experiments(experiments):
    experimentsList = [];
    for (key,val) in experiments.items():
        experimentsList.append({                    
            "hash": key,
            "rating": val
        });
    st.session_state.correctness_tuples = experimentsList;
    st.session_state.all_correctness_experiments = experimentsList;

def filter_experiments(): # either 0.5 or 1.0 or 1.25 or 1.5
    current_selection = st.session_state['experiment_selection']
    selection_hash_list = [];
    for (key,val) in st.session_state.metadata_dict.items():
        metadata = val['metadata'];
        if str(current_selection) in metadata:
            selection_hash_list.append(key);
    st.session_state.correctness_tuples = [x for x in st.session_state.all_correctness_experiments if x["hash"] in selection_hash_list]

def fetch_user_information(response):
    id = response.json()["id"];
    st.session_state.user_id = id;
    setup_c_experiments(response.json()["correctnessExperiments"]);
    setup_u_experiments(response.json()["understandabilityExperiments"]);
    filter_experiments();

def show_correctness_metric():
    if st.session_state.correctness_tuples is not None:
        show_explanations_for_correctness(); # Pass parameter, concrete tuple

def compute_done_experiments():
    # Compute for correctness
    cor_done = 0
    for i in range(len(st.session_state.correctness_tuples)):
        if st.session_state.correctness_tuples[i]["rating"] > -1:
            cor_done += 1;
    st.session_state.correctness_done = cor_done;

    # Compute for understandability
    und_done = 0
    for i in range(len(st.session_state.understandability_tuples)):
        if st.session_state.understandability_tuples[i]["best"] is not None and st.session_state.understandability_tuples[i]["worst"] is not None:
            und_done += 1;
    st.session_state.understandability_done = und_done;

def show_explanations_for_correctness():
    previous, current, next = st.columns([.1, .8, .1])
    errorsInput = st.empty();
    with previous:
        st.button("Previous", on_click=lambda: decrement_correctness(0, errorsInput), key="previous")
    with current:
        st.text_area(label="Area", label_visibility='hidden', value=f"{st.session_state.hash_explanation_dict[st.session_state.correctness_tuples[st.session_state.current_correctness_index]['hash']][1]}", height=300)
        #code_editor(f"{st.session_state.hash_explanation_dict[tuples[st.session_state.current_correctness_index]][1]}", height=50, lang='text', theme="default", options={"wrap": True})
        placeholder, errors, placeholder2 = st.columns([.3,.4,.3])
        with errors:
            errorsInput = st.text_input(label="Errors", key=st.session_state.correctness_tuples[st.session_state.current_correctness_index], value=st.session_state.correctness_tuples[st.session_state.current_correctness_index]['rating']);
    with next:
        col1, col2 = st.columns([.5,.5])
        with col2:
            st.button("Next", on_click=lambda: increment_correctness(len(st.session_state.correctness_tuples), errorsInput), key="next")

    st.divider();

    input_data, output_data = st.columns(2)
    with input_data:
        st.markdown('<h3 style="text-align: center;">Input data</h2>', unsafe_allow_html=True)
        st.text_area(label="Area", label_visibility='hidden', value=f"{st.session_state.hash_explanation_dict_inputdata[st.session_state.correctness_tuples[st.session_state.current_correctness_index]['hash']][1]}", height=400)
        #code_editor(f"{st.session_state.hash_explanation_dict_inputdata[tuples[st.session_state.current_correctness_index]][1]}" ,lang='text', theme="default", options={"wrap": True})
    with output_data:
        st.markdown('<h3 style="text-align: center;">Output data</h2>', unsafe_allow_html=True)
        st.text_area(label="Area", label_visibility='hidden', value=f"{st.session_state.hash_explanation_dict_outputdata[st.session_state.correctness_tuples[st.session_state.current_correctness_index]['hash']][1]}", height=400)
        #code_editor(f"{st.session_state.hash_explanation_dict_outputdata[tuples[st.session_state.current_correctness_index]][1]}", lang='text', theme="default", options={"wrap": True})     

def increment_correctness(max, rating):
    try:
        store_rating(rating);
        if st.session_state.current_correctness_index < max:
            st.session_state.current_correctness_index += 1;
        else:
            st.session_state.current_correctness_index = 0;
    except Exception as e:
        st.toast(str(e));

def store_rating(rating_str):
    current_hash = st.session_state.correctness_tuples[st.session_state.current_correctness_index]["hash"];
    current_id = st.session_state.user_id;
    try:
        rating = int(rating_str);
        if not 0 <= rating <= 100:
            st.toast("Skipped experiment as the value must be a positive integer");
            return None;
        response = requests.post(f"{BACKEND_URL}/storecorrectness/{current_id}/{current_hash}/{rating}");
        if 200 <= response.status_code < 300:
            st.session_state.correctness_tuples[st.session_state.current_correctness_index]["rating"] = rating;
            print("Stored errors for explanations with hash ", st.session_state.correctness_tuples[st.session_state.current_correctness_index]["hash"], ": ", rating);
            compute_done_experiments();
    except ValueError as e:
        raise Exception("The passed value isn't a integer, error: " + e);

def decrement_correctness(min, rating):
    try:
        store_rating(rating);
        if st.session_state.current_correctness_index > min:
            st.session_state.current_correctness_index -= 1;
        else:
            st.session_state.current_correctness_index = len(st.session_state.correctness_tuples) - 1;
    except Exception as e:
        st.toast(str(e));

def show_understandability_metric():
    if st.session_state.understandability_tuples is not None:
        show_explanations(st.session_state.understandability_tuples[st.session_state.current_understandability_index]["tuple"],"bws"); # Pass parameter, concrete tuple
        st.divider();
        placeholder, button1, currentIndex, button2, placeholder2 = st.columns([.35,.1,.1,.1,.35])
        with button1:   
            st.button("Previous", on_click=lambda: previous_understandability_explanation())
        with currentIndex:
            col1, col2, col3 = st.columns([.3,.4,.3])
            with col2:
                st.text(f"{st.session_state.current_understandability_index+1}")
        with button2:
            st.button("Next", on_click=lambda: next_understandability_explanation())

def next_understandability_explanation():
    # Store current best and worst
    data = {
        "best": st.session_state.best_worst_current["best"],
        "worst": st.session_state.best_worst_current["worst"]
    }
    response = requests.post(f"{BACKEND_URL}/storeunderstandability/{st.session_state.user_id}/{st.session_state.best_worst_current['tuple']}",json=data, headers={"Content-Type": "application/json"});    
    if 200 <= response.status_code < 300:
        print("Stored best and worst explanations successfully");
        st.session_state.understandability_tuples[st.session_state.current_understandability_index]["best"] = data["best"];
        st.session_state.understandability_tuples[st.session_state.current_understandability_index]["worst"] = data["worst"];
        if(st.session_state.current_understandability_index < len(st.session_state.understandability_tuples) - 1):
            st.session_state.current_understandability_index += 1;
        else:
            st.session_state.current_understandability_index = 0;
        st.session_state.best_worst_current = {
            "tuple": st.session_state.understandability_tuples[st.session_state.current_understandability_index]["tuple"],
            "best": st.session_state.understandability_tuples[st.session_state.current_understandability_index]["best"],
            "worst": st.session_state.understandability_tuples[st.session_state.current_understandability_index]["worst"]   
        };
        compute_done_experiments();
    else:
        st.toast("Error at storing the best and worst explanations");

    
def previous_understandability_explanation():
    data = {
        "best": st.session_state.best_worst_current["best"],
        "worst": st.session_state.best_worst_current["worst"]
    };
    if(st.session_state.current_understandability_index > 0):
        response = requests.post(f"{BACKEND_URL}/storeunderstandability/{st.session_state.user_id}/{st.session_state.best_worst_current['tuple']}",json=data, headers={"Content-Type": "application/json"});
        if 200 <= response.status_code < 300:
            print("Stored best and worst explanations successfully");
            st.session_state.understandability_tuples[st.session_state.current_understandability_index]["best"] = data["best"];
            st.session_state.understandability_tuples[st.session_state.current_understandability_index]["worst"] = data["worst"];
            st.session_state.current_understandability_index -= 1;
            st.session_state.best_worst_current = {
                "tuple": st.session_state.understandability_tuples[st.session_state.current_understandability_index]["tuple"],
                "best": st.session_state.understandability_tuples[st.session_state.current_understandability_index]["best"],
                "worst": st.session_state.understandability_tuples[st.session_state.current_understandability_index]["worst"]   
            };
            compute_done_experiments();
        else:
            st.toast("Error at storing the best and worst explanations");
    else:
        st.toast("You are at the beginning of the list");        

def show_bws_rating_scale(key): #The key represents the hash
    placeholder, best, worst, placeholder2 = st.columns([.4,.1,.1,.4])
    with best:
        if st.session_state.best_worst_current["best"] == key:
            st.button("Best", key=key + "_best", on_click=lambda: store_best(key), type='primary')
        else:
            st.button("Best", key=key + "_best", on_click=lambda: store_best(key))
    with worst: 
        if st.session_state.best_worst_current["worst"] == key:
            st.button("Worst", key=key + "_worst", on_click=lambda: store_worst(key), type='primary')
        else:
            st.button("Worst", key=key + "_worst", on_click=lambda: store_worst(key))

def store_best(key):
    st.session_state.best_worst_current["best"] = key;
    st.toast(f"You select the explanation {key} as the best explanation");

def store_worst(key):
    st.session_state.best_worst_current["worst"] = key;
    st.toast(f"You select the explanation {key} as the worst explanation");


def show_error_rating_scale():
    st.write("Error Rating Scale");

def show_explanations(tuple, type):

    # Pre-process the tuple
    tupleFixed = tuple.split("-");

    st.session_state.best_worst_current["tuple"] = tuple;

    col1, col2 = st.columns([.5,.5])
    with col1:
        st.text_area(label="Area", label_visibility='hidden', value=f"{st.session_state.hash_explanation_dict[tupleFixed[0]][1]}", height=300)
        show_bws_rating_scale(tupleFixed[0]);
    with col2:
        st.text_area(label="Area", label_visibility='hidden', value=f"{st.session_state.hash_explanation_dict[tupleFixed[1]][1]}", height=300)
        show_bws_rating_scale(tupleFixed[1]);
        
    col3, col4 = st.columns([.5,.5])
    with col3:
        st.text_area(label="Area", label_visibility='hidden', value=f"{st.session_state.hash_explanation_dict[tupleFixed[2]][1]}", height=300)
        show_bws_rating_scale(tupleFixed[2]);
    with col4:
        st.text_area(label="Area", label_visibility='hidden', value=f"{st.session_state.hash_explanation_dict[tupleFixed[3]][1]}", height=300)
        show_bws_rating_scale(tupleFixed[3]);
    
    col5, col6 = st.columns([.5,.5])
    with col5:
        st.text_area(label="Area", label_visibility='hidden', value=f"{st.session_state.hash_explanation_dict[tupleFixed[4]][1]}", height=300)
        show_bws_rating_scale(tupleFixed[4]);
        

def login_user(user_id):
    response = requests.post(f"{BACKEND_URL}/login/{user_id}");
    if 200 <= response.status_code < 300:
        print("Login successful");
        fetch_user_information(response);

with st.sidebar:
    st.subheader("User")
    if st.session_state.user_id is not None:
        st.text(f"User ID: {st.session_state.user_id}")#
        st.subheader("Done evaluated experiments")
        st.text(f"Correctness: {st.session_state.correctness_done}/{len(st.session_state.correctness_tuples)}");
        st.text(f"Understandability: {st.session_state.understandability_done}/{len(st.session_state.understandability_tuples)}");
        selection = st.selectbox("Filter experiments", options=[0.5, 1.0, 1.25, 1.5], index=1, on_change=filter_experiments, key='experiment_selection')
    else:
        user_input = st.text_input("User ID", help="Enter your user ID")
        st.button("Login", on_click=lambda: login_user(user_input))

    #st.text(f"Correctness: {st.session_state.correctness_done}/{st.session_state.number_of_correctness}")
    #st.text(f"Understandability: {st.session_state.understandability_done}/{st.session_state.number_of_understandability}")
    #st.button("Create new user", on_click=lambda: create_user(), help="Creates a new user ID with \n a new experimental setting")
    st.button("Switch metric", on_click=lambda: switch_metric(), help="Switches between correctness and understandability")

if st.session_state.current_metric == "Correctness":
    show_correctness_metric();
elif st.session_state.current_metric == "Understandability":                
    show_understandability_metric();



####### Explanations reagrding the correctness dict #######

# correctness_tuples
## hash::String, rating ::int

# understandability_tuples
#{
#    tuple::String[],
#    best::String,
#    worst::String
#}