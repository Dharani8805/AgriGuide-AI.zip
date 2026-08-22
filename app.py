import os
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv
from google import genai

load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY) if API_KEY else None

SYSTEM_PROMPT = """
You are AgriGuide AI, a domain-specific agriculture information assistant.

Your job is to answer questions about:
- crop care and plant health
- soil preparation and soil improvement
- irrigation and watering
- fertilizers, compost, and manure
- pest and disease prevention/management
- harvesting and basic farming practices
- crop rotation and sustainable agriculture

Stay strictly focused on agriculture. If a question is unrelated, politely explain
that you only provide agriculture information and invite an agriculture-related question.

Give simple, practical, beginner-friendly answers. Avoid pretending to diagnose a crop
problem with certainty from limited information. For serious crop damage, suspected
disease outbreaks, or situations requiring local diagnosis, recommend contacting a
qualified agricultural officer, agronomist, horticulturist, or other local agriculture
professional.

For pesticides, herbicides, fungicides, and other agricultural chemicals:
- recommend integrated pest management (IPM) and non-chemical options first when practical;
- tell users to follow the product label and local regulations;
- recommend appropriate protective equipment;
- never suggest unsafe mixing or off-label use;
- advise users to consult a qualified professional when the crop/problem is serious.

Do not provide medical, legal, financial, or unrelated advice.
"""

FALLBACK_RESPONSES = {
    "irrigation": """For most crops, water when the soil moisture in the crop's root zone is getting low rather than following a fixed schedule.

Practical tips:
- Check the soil a few centimeters below the surface before watering.
- Water deeply enough to wet the main root zone, then allow appropriate drainage.
- Sandy soils usually need more frequent watering than heavier soils.
- Avoid prolonged waterlogging because it can reduce root oxygen and encourage root diseases.
- Water early in the morning when practical to reduce evaporation.

The exact amount and frequency depend on the crop, soil, weather, growth stage, and irrigation method.""",

    "soil": """To improve soil health:
- Add well-decomposed compost or suitable organic matter.
- Keep the soil covered with mulch where appropriate.
- Rotate crops and include suitable legumes where they fit your farming system.
- Avoid unnecessary tillage and compaction.
- Maintain good drainage and prevent erosion.
- Consider a soil test before making major fertilizer or amendment decisions.

Avoid adding large amounts of fertilizer based only on guesswork; nutrient needs vary by crop and soil.""",

    "fertilizer": """Use fertilizers and manure according to the crop's nutrient needs and, ideally, a soil test.

A simple approach:
- Use well-decomposed manure or compost rather than fresh manure around growing plants.
- Apply the correct nutrient source at the recommended rate and timing.
- Do not assume more fertilizer means more yield; excess nutrients can damage plants and pollute water.
- Keep fertilizer away from direct contact with stems when the product instructions require it.
- Follow the label for commercial fertilizers and local agricultural recommendations.""",

    "pest": """Start with integrated pest management (IPM):
- Inspect plants regularly and identify the pest before treating.
- Remove badly affected plant parts when appropriate.
- Keep fields/gardens clean and remove crop residues that can harbor pests when appropriate.
- Encourage beneficial insects and use physical barriers or traps where suitable.
- Rotate crops to reduce recurring pest pressure.
- Use pesticides only when needed, and follow the product label, local regulations, and required protective equipment.

For severe or rapidly spreading infestations, get a qualified local agriculture professional to identify the pest and recommend an appropriate treatment.""",

    "general": """Good basic farming practice starts with matching the crop to the local climate and soil, maintaining healthy soil, managing water carefully, monitoring plants regularly, and using nutrients based on crop needs.

Useful habits include crop rotation, compost or suitable organic matter, mulching, integrated pest management, erosion control, and timely harvesting.

For a more specific recommendation, include the crop, location/climate, soil type if known, growth stage, and the main problem you are seeing."""
}


def local_fallback(question):
    q = question.lower()

    if any(word in q for word in [
        "water", "watering", "irrigation", "irrigate", "dry", "moisture"
    ]):
        return FALLBACK_RESPONSES["irrigation"]

    if any(word in q for word in [
        "soil", "compost", "organic matter", "mulch", "erosion", "rotation"
    ]):
        return FALLBACK_RESPONSES["soil"]

    if any(word in q for word in [
        "fertilizer", "fertiliser", "manure", "compost", "nutrient", "npk"
    ]):
        return FALLBACK_RESPONSES["fertilizer"]

    if any(word in q for word in [
        "pest", "insect", "aphid", "caterpillar", "fungus", "fungal",
        "disease", "weed", "mite", "borer"
    ]):
        return FALLBACK_RESPONSES["pest"]

    return FALLBACK_RESPONSES["general"]


def ask_gemini(question):
    if not client:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    # A current Gemini model name can be changed here if needed.
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"{SYSTEM_PROMPT}\n\nUser question:\n{question}",
    )

    text = getattr(response, "text", None)
    if not text:
        raise RuntimeError("Gemini returned an empty response.")

    return text.strip()


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    question = str(data.get("message", "")).strip()

    if not question:
        return jsonify({
            "response": "Please enter an agriculture-related question."
        }), 400

    if len(question) > 4000:
        return jsonify({
            "response": "Please keep your question under 4,000 characters."
        }), 400

    try:
        answer = ask_gemini(question)
        source = "gemini"
    except Exception:
        # Quota, API, network, model, missing-key, and other Gemini failures
        # are intentionally handled by the local agriculture fallback.
        answer = local_fallback(question)
        source = "fallback"

    return jsonify({
        "response": answer,
        "source": source
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
