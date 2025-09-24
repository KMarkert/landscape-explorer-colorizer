import base64
from dataclasses import field
import io
import os
import inspect

import ee
import mesop as me
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.staticfiles import StaticFiles
from google import genai
from PIL import Image
from dotenv import load_dotenv
from typing import Callable
import mesop.events as me_events
from google_maps_component import google_maps_component

# Load environment variables from .env file
load_dotenv()

# Initialize the FastAPI app
app = FastAPI()

# Initialize Earth Engine
try:
    ee.Initialize(project='georeason-app-demo')
except ee.EEException:
    ee.Authenticate()
    ee.Initialize(project='georeason-app-demo')

# Configure the Gemini client
client = genai.Client()


# Define the state for our application
@me.stateclass
class State:
    original_image: str = ""
    colorized_image: str = ""
    loading: bool = False
    lat: float = 0.0
    lng: float = 0.0
    marker: dict[str, float] = field(default_factory=dict)
    box: dict[str, float]  = field(default_factory=dict)
    show_instructions: bool = True
    show_images: bool = False
    show_layer: bool = True
    layer_opacity: float = 1.0


async def on_map_click(e: me.WebEvent):
    """Event handler for map clicks."""
    lat,lng = e.value["lat"], e.value["lng"]
    state = me.state(State)
    state.lat = lat
    state.lng = lng
    state.loading = True
    state.original_image = None
    state.colorized_image = None
 
    # Calculate 1km box
    bounds = ee.Geometry.Point(lng, lat).buffer(1000).bounds().getInfo()['coordinates'][0]
    state.box = {
        "north": bounds[2][1],
        "south": bounds[0][1],
        "east": bounds[1][0],
        "west": bounds[0][0],
    }

    # Yield to update the UI with the loading state
    yield

    # Fetch and process the image
    await get_and_colorize_image()
    yield


async def get_and_colorize_image():
    """Fetches an image from Earth Engine and colorizes it with Gemini."""
    state = me.state(State)
    try:
        # 1. Fetch image from Earth Engine
        # point = ee.Geometry.Point(state.lng, state.lat)
        roi = ee.Geometry.Rectangle([state.box["west"], state.box["south"], state.box["east"], state.box["north"]])
        image_collection = ee.ImageCollection("projects/wlfw-um/assets/historical-imagery/conus-west")
        image = image_collection.mosaic().clipToBoundsAndScale(roi, scale=1)
        
        png_bytes = ee.data.computePixels({
            'expression': image,
            'fileFormat': 'PNG',
        })
        
        original_pil_image = Image.open(io.BytesIO(png_bytes))
        state.original_image = pil_to_base64(original_pil_image)

        # 2. Colorize with Gemini
        prompt = (
            f"A photorealistic colorization of a black and white aerial image from the 1950s. "
            f"The scene is a landscape near latitude {state.lat} and longitude {state.lng}. "
            f"The colorization should be realistic, with natural-looking colors for the vegetation, soil, and water. "
            f"The lighting should be consistent with a input image."
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash-image-preview",
            contents=[prompt, original_pil_image],
        )

        colorized_pil_image = None
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                colorized_pil_image = Image.open(io.BytesIO(part.inline_data.data))
                break
        
        if colorized_pil_image:
            state.colorized_image = pil_to_base64(colorized_pil_image)
            state.show_images = True

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        state.loading = False


def pil_to_base64(img: Image.Image) -> str:
    """Converts a PIL Image to a base64 encoded string."""
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffered.getvalue()).decode("utf-8")

def get_linkedin_url():
    return "https://www.linkedin.com/sharing/share-offsite/?url=http://localhost:8000"

def get_email_url():
    subject = "Check out this cool Landscape Colorizer!"
    body = "I found this cool app that colorizes black and white aerial imagery from the 1950s. Check it out: http://localhost:8000"
    return f"mailto:?subject={subject}&body={body}"

async def show_instructions(e: me.ClickEvent):
    """Shows the instructions modal."""
    me.state(State).show_instructions = True

async def hide_instructions(e: me.ClickEvent):
    """Hides the instructions modal."""
    me.state(State).show_instructions = False

async def show_images(e: me.ClickEvent):
    """Shows the images modal."""
    me.state(State).show_images = True

async def hide_images(e: me.ClickEvent):
    """Hides the images modal."""
    me.state(State).show_images = False

async def toggle_layer(e: me.CheckboxChangeEvent):
    """Toggles the XYZ layer visibility."""
    me.state(State).show_layer = e.checked

async def change_opacity(e):
    """Changes the XYZ layer opacity."""
    me.state(State).layer_opacity = e.value


@me.page(
    path="/",
    title="Landscape Explorer Colorizer",
    security_policy=me.SecurityPolicy(
        dangerously_disable_trusted_types=True,
        allowed_script_srcs=["https://maps.googleapis.com", "https://cdn.jsdelivr.net"],
        allowed_connect_srcs=["https://maps.googleapis.com"],
    ),
)
def page():
    """Defines the main UI of the application."""
    state = me.state(State)
    maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")

    image_collection = ee.ImageCollection("projects/wlfw-um/assets/historical-imagery/conus-west")
    map_id = image_collection.getMapId()

    with me.box(
        style=me.Style(
            display="flex",
            flex_direction="column",
            font_family="Google Sans",
            background="#fff" if me.theme_brightness() == "light" else "#121212",
            height="100%",
        )
    ):

        with me.box(key="header", style=me.Style(position="absolute", top=0, left=0, right=0, height="80px", background="white", padding=me.Padding.all(16))):
            me.text("Landscape Explorer Colorizer", type="headline-4")

        with me.box(
            key="main_container",
            style=me.Style(
                width="100%",
                height="100%",
                flex_grow=1,
                display="flex",
                flex_direction="row",
                overflow_x="hidden",
                overflow_y="hidden",
            ),
        ):

            with me.box(key="map_container", style=me.Style(position="absolute", top="80px", height="calc(100% - 80px)", width="100%")):
                with me.box(key="map", style=me.Style(height="100%", width="100%")):
                    google_maps_component(
                        api_key=maps_api_key,
                        on_click=on_map_click,
                        marker={"lat": state.lat, "lng": state.lng},
                        box=me.state(State).box,
                        map_id=map_id["mapid"],
                        show_layer=state.show_layer,
                        layer_opacity=state.layer_opacity,
                    )

    with me.box(style=me.Style(position="absolute", top=16, right=16)):
        me.button("Instructions", on_click=show_instructions)

    with me.box(style=me.Style(position="absolute", bottom=32, left=16)):
        with me.expansion_panel(title="Layers", icon="layers"):
            me.checkbox(label="Historical Imagery", on_change=toggle_layer, checked=state.show_layer)
            me.slider(
                key=f"layer_slider",
                min=0.0,
                max=1.0,
                step=0.1,
                value=state.layer_opacity,
                on_value_change=change_opacity,
                style=me.Style(width="100px", right=0),
            )

    if state.show_instructions:
        with me.box(
            style=me.Style(
                position="absolute",
                top="50%",
                left="50%",
                transform="translate(-50%, -50%)",
                background="white",
                padding=me.Padding.all(16),
                border_radius=8,
                z_index=10,
            )
        ):
            me.markdown(
                "# Instructions "
                "\n "
                "## Intro "
                "\n "
                "Explore past landscapes from the Great Plains to the Pacific "
                "coast in a new lens. This application takes historic black and "
                "white aerial imagery and uses AI to restore the imagery and see "
                "how landscapes have changed since the mid-20th century. "
                "Data and motiviation is from the "
                "[Landscape Explorer](https://www.landscapeexplorer.org/) "
                "\n "
                "## How-to use" 
                "\n "
                "Click on the map to select a location. The application will "
                "fetch the black and white aerial image and use the nano banana "
                "🍌 model to colorize it. "
                "\n "
                "The map shows the historical image by default, adjust the layer "
                "opacity or turn on/off to see what the aerial imagery is today. "
            )
            with me.box(style=me.Style(display="flex", justify_content="flex-end", margin=me.Margin(top=16))):
                me.button("Close", on_click=hide_instructions)

    if state.loading:
        with me.box(style=me.Style(position="absolute", top="50%", left="50%", transform="translate(-50%, -50%)", background="white", padding=me.Padding.all(16), border_radius=8)):
            with me.box(style=me.Style(display="flex", justify_content="center", align_items="center")):
                me.progress_spinner()
                me.text("Fetching and colorizing image...", style=me.Style(margin=me.Margin(left=16)))
    
    if state.original_image or state.colorized_image:
        with me.box(style=me.Style(position="absolute", top=96, right=16)):
            me.button("Show Images", on_click=show_images, style=me.Style(background="white"))

    if state.show_images:
        with me.box(
            style=me.Style(
                position="absolute",
                top="50%",
                left="50%",
                transform="translate(-50%, -50%)",
                background="white",
                padding=me.Padding.all(16),
                border_radius=8,
                z_index=10,
                width="80%",
                max_width="1200px",
            )
        ):
            with me.box(style=me.Style(display="flex", justify_content="space-between", align_items="center", margin=me.Margin(bottom=16))):
                me.text("Images", type="headline-6")
                me.button("Close", on_click=hide_images)
            with me.box(style=me.Style(display="grid", grid_template_columns="1fr 1fr", gap="16px", justify_items="center")):
                if state.original_image:
                    with me.box():
                        me.text("Original (1950s)", type="headline-6", style=me.Style(margin=me.Margin(bottom='32px')))
                        me.image(src=state.original_image, style=me.Style(width="100%", height="auto", max_height="400px"))
                if state.colorized_image:
                    with me.box():
                        with me.box(style=me.Style(display="flex", justify_content="space-between", align_items="center", margin=me.Margin(bottom=16))):
                            me.text("Colorized (AI)", type="headline-6")
                            with me.box(style=me.Style(display="flex", gap="16px")):
                                me.html(f'<a href="{state.colorized_image}" download="colorized_image.png"><button>Download</button></a>')
                                # me.html(f'<a href="{get_linkedin_url()}" target="_blank"><button>Share on LinkedIn</button></a>')
                                # me.html(f'<a href="{get_email_url()}"><button>Share via Email</button></a>')
                        me.image(src=state.colorized_image, style=me.Style(width="100%", height="auto", max_height="400px"))


# --- FastAPI Server Setup ---

# Mount the Mesop static files.
app.mount(
    "/static",
    StaticFiles(
        directory=os.path.join(
            os.path.dirname(inspect.getfile(me)), "web", "src", "app", "prod", "web_package"
        )
    ),
    name="static",
)

# Mount the local project directory to serve web component JS files.
app.mount(
    "/",
    WSGIMiddleware(me.create_wsgi_app(debug_mode=True)),
)
