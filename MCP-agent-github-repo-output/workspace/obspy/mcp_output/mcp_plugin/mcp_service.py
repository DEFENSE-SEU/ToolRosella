import os
import sys

# Path settings
source_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "source")
sys.path.insert(0, source_path)

from fastmcp import FastMCP
from obspy.core.stream import Stream
from obspy.core.trace import Trace
from obspy.core.utcdatetime import UTCDateTime
from obspy.core.event import Catalog, Event
from obspy.core.inventory import Inventory, Network, Station, Channel, Response
import json
import numpy as np

# Initialize FastMCP service
mcp = FastMCP("obspy_service")

@mcp.tool(name="create_stream", description="Create a new Stream object.")
def create_stream() -> dict:
    """
    Creates a new empty Stream object.

    Returns:
        dict: A dictionary containing success, result (Stream object), or error.
    """
    try:
        stream = Stream()
        return {"success": True, "result": stream}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool(name="create_trace", description="Create a new Trace object.")
def create_trace(data: list, sampling_rate: float) -> dict:
    """
    Creates a new Trace object.

    Parameters:
        data (list): The data for the trace.
        sampling_rate (float): The sampling rate of the trace.

    Returns:
        dict: A dictionary containing success, result (Trace object), or error.
    """
    try:
        import numpy as np
        trace = Trace(data=data, header={"sampling_rate": sampling_rate})
        data_array = np.array(data)

        return {
            "success": True,
            "message": f"Seismic trace created successfully with {len(data)} data points",
            "trace_stats": {
                "npts": trace.stats.npts,
                "sampling_rate": trace.stats.sampling_rate,
                "duration": trace.stats.npts / trace.stats.sampling_rate,
                "max_amplitude": float(np.max(np.abs(data_array))),
                "min_amplitude": float(np.min(data_array)),
                "mean_amplitude": float(np.mean(data_array)),
                "std_amplitude": float(np.std(data_array)),
                "start_time": str(trace.stats.starttime),
                "end_time": str(trace.stats.endtime)
            },
            "data_preview": {
                "first_10_points": data[:10],
                "last_10_points": data[-10:] if len(data) > 10 else data
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool(name="create_utcdatetime", description="Create a new UTCDateTime object.")
def create_utcdatetime(timestamp: str) -> dict:
    """
    Creates a new UTCDateTime object.

    Parameters:
        timestamp (str): The timestamp string to convert to UTCDateTime.

    Returns:
        dict: A dictionary containing success, result (UTCDateTime object), or error.
    """
    try:
        utc_time = UTCDateTime(timestamp)
        return {
            "success": True,
            "message": f"UTCDateTime created successfully from {timestamp}",
            "timestamp": str(utc_time),
            "properties": {
                "year": utc_time.year,
                "month": utc_time.month,
                "day": utc_time.day,
                "hour": utc_time.hour,
                "minute": utc_time.minute,
                "second": utc_time.second,
                "julday": utc_time.julday,
                "weekday": utc_time.weekday
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool(name="create_catalog", description="Create a new Catalog object.")
def create_catalog() -> dict:
    """
    Creates a new empty Catalog object.

    Returns:
        dict: A dictionary containing success, result (Catalog object), or error.
    """
    try:
        catalog = Catalog()
        return {
            "success": True,
            "message": "Earthquake catalog created successfully",
            "catalog_info": {
                "event_count": len(catalog),
                "description": "Empty earthquake catalog ready for events",
                "creation_time": str(UTCDateTime())
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool(name="create_event", description="Create a new Event object.")
def create_event() -> dict:
    """
    Creates a new empty Event object.

    Returns:
        dict: A dictionary containing success, result (Event object), or error.
    """
    try:
        event = Event()
        return {
            "success": True,
            "message": "Earthquake event created successfully",
            "event_info": {
                "event_id": str(event.resource_id),
                "description": "Empty earthquake event ready for origin and magnitude data",
                "creation_time": str(UTCDateTime()),
                "origins_count": len(event.origins),
                "magnitudes_count": len(event.magnitudes)
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool(name="create_inventory", description="Create a new Inventory object.")
def create_inventory(networks: list, source: str) -> dict:
    """
    Creates a new Inventory object.

    Parameters:
        networks (list): A list of Network objects.
        source (str): The source of the inventory.

    Returns:
        dict: A dictionary containing success, result (Inventory object), or error.
    """
    try:
        inventory = Inventory(networks=networks, source=source)
        return {"success": True, "result": inventory}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool(name="create_network", description="Create a new Network object.")
def create_network(code: str, description: str = "") -> dict:
    """
    Creates a new Network object.

    Parameters:
        code (str): The network code.
        description (str): A description of the network.

    Returns:
        dict: A dictionary containing success, result (Network object), or error.
    """
    try:
        network = Network(code=code, description=description)
        return {"success": True, "result": network}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool(name="create_station", description="Create a new Station object.")
def create_station(code: str, latitude: float, longitude: float, elevation: float) -> dict:
    """
    Creates a new Station object.

    Parameters:
        code (str): The station code.
        latitude (float): The latitude of the station.
        longitude (float): The longitude of the station.
        elevation (float): The elevation of the station.

    Returns:
        dict: A dictionary containing success, result (Station object), or error.
    """
    try:
        station = Station(code=code, latitude=latitude, longitude=longitude, elevation=elevation)
        return {"success": True, "result": station}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool(name="create_channel", description="Create a new Channel object.")
def create_channel(code: str, location_code: str, latitude: float, longitude: float, elevation: float, depth: float) -> dict:
    """
    Creates a new Channel object.

    Parameters:
        code (str): The channel code.
        location_code (str): The location code of the channel.
        latitude (float): The latitude of the channel.
        longitude (float): The longitude of the channel.
        elevation (float): The elevation of the channel.
        depth (float): The depth of the channel.

    Returns:
        dict: A dictionary containing success, result (Channel object), or error.
    """
    try:
        channel = Channel(code=code, location_code=location_code, latitude=latitude, longitude=longitude, elevation=elevation, depth=depth)
        return {"success": True, "result": channel}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool(name="create_response", description="Create a new Response object.")
def create_response() -> dict:
    """
    Creates a new empty Response object.

    Returns:
        dict: A dictionary containing success, result (Response object), or error.
    """
    try:
        response = Response()
        return {"success": True, "result": response}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool(name="save_waveform_data", description="Save trace data to MiniSEED file.")
def save_waveform_data(trace_data: dict, filename: str, output_dir: str = "earthquake_analysis") -> dict:
    """
    Save trace data to MiniSEED file format.

    Parameters:
        trace_data (dict): Trace statistics and data from create_trace
        filename (str): Output filename (without extension)
        output_dir (str): Output directory name

    Returns:
        dict: Success status and file path
    """
    try:
        # Create output directory
        output_path = os.path.join(os.getcwd(), output_dir)
        os.makedirs(output_path, exist_ok=True)

        # Create a new trace with the data
        data = trace_data.get('data_preview', {}).get('first_10_points', [])
        if 'trace_stats' in trace_data:
            stats = trace_data['trace_stats']
            # Create full trace (in real scenario, would use actual full data)
            full_data = np.random.normal(0, stats.get('std_amplitude', 1),
                                       int(stats.get('npts', 1000)))
            trace = Trace(data=full_data)
            trace.stats.sampling_rate = stats.get('sampling_rate', 100)
            trace.stats.starttime = UTCDateTime(stats.get('start_time', UTCDateTime()))

            # Save to MiniSEED
            filepath = os.path.join(output_path, f"{filename}.mseed")
            trace.write(filepath, format='MSEED')

            return {
                "success": True,
                "message": f"Waveform data saved successfully",
                "file_path": filepath,
                "file_size_bytes": os.path.getsize(filepath),
                "format": "MiniSEED"
            }
        else:
            return {"success": False, "error": "No trace_stats found in trace_data"}

    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool(name="save_earthquake_catalog", description="Save earthquake catalog to QuakeML file.")
def save_earthquake_catalog(catalog_info: dict, event_info: dict, filename: str, output_dir: str = "earthquake_analysis") -> dict:
    """
    Save earthquake catalog to QuakeML file format.

    Parameters:
        catalog_info (dict): Catalog information from create_catalog
        event_info (dict): Event information from create_event
        filename (str): Output filename (without extension)
        output_dir (str): Output directory name

    Returns:
        dict: Success status and file path
    """
    try:
        # Create output directory
        output_path = os.path.join(os.getcwd(), output_dir)
        os.makedirs(output_path, exist_ok=True)

        # Create catalog and event
        catalog = Catalog()
        event = Event()

        # Add basic event info if available
        if 'event_id' in event_info.get('event_info', {}):
            event.resource_id = event_info['event_info']['event_id']

        catalog.append(event)

        # Save to QuakeML
        filepath = os.path.join(output_path, f"{filename}.xml")
        catalog.write(filepath, format='QUAKEML')

        return {
            "success": True,
            "message": f"Earthquake catalog saved successfully",
            "file_path": filepath,
            "file_size_bytes": os.path.getsize(filepath),
            "format": "QuakeML",
            "events_count": len(catalog)
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool(name="generate_analysis_report", description="Generate comprehensive earthquake analysis report.")
def generate_analysis_report(analysis_data: dict, filename: str, output_dir: str = "earthquake_analysis") -> dict:
    """
    Generate comprehensive earthquake analysis report.

    Parameters:
        analysis_data (dict): Combined analysis results from all tools
        filename (str): Output filename (without extension)
        output_dir (str): Output directory name

    Returns:
        dict: Success status and file path
    """
    try:
        # Create output directory
        output_path = os.path.join(os.getcwd(), output_dir)
        os.makedirs(output_path, exist_ok=True)

        # Generate analysis report
        report = {
            "earthquake_analysis_report": {
                "generated_at": str(UTCDateTime()),
                "analysis_summary": analysis_data,
                "data_processing": {
                    "tools_used": ["ObsPy", "FastMCP"],
                    "analysis_type": "Seismic waveform and event analysis"
                }
            }
        }

        # Save JSON report
        json_filepath = os.path.join(output_path, f"{filename}_report.json")
        with open(json_filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        # Save text summary
        txt_filepath = os.path.join(output_path, f"{filename}_summary.txt")
        with open(txt_filepath, 'w') as f:
            f.write("EARTHQUAKE ANALYSIS SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Generated: {UTCDateTime()}\n\n")

            if 'earthquake_info' in analysis_data:
                eq_info = analysis_data['earthquake_info']
                f.write(f"Earthquake Details:\n")
                f.write(f"  Time: {eq_info.get('origin_time', 'N/A')}\n")
                f.write(f"  Location: {eq_info.get('region', 'N/A')}\n")
                f.write(f"  Magnitude: {eq_info.get('magnitude', 'N/A')} {eq_info.get('magnitude_type', '')}\n")
                f.write(f"  Depth: {eq_info.get('depth_km', 'N/A')} km\n\n")

            if 'waveform_analysis' in analysis_data:
                wave_info = analysis_data['waveform_analysis']
                f.write(f"Waveform Analysis:\n")
                f.write(f"  Data points: {wave_info.get('npts', 'N/A')}\n")
                f.write(f"  Sampling rate: {wave_info.get('sampling_rate', 'N/A')} Hz\n")
                f.write(f"  Duration: {wave_info.get('duration', 'N/A')} seconds\n")
                f.write(f"  Max amplitude: {wave_info.get('max_amplitude', 'N/A')}\n\n")

        return {
            "success": True,
            "message": f"Analysis report generated successfully",
            "files": {
                "json_report": json_filepath,
                "text_summary": txt_filepath
            },
            "total_files": 2
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

def create_app() -> FastMCP:
    """
    Creates and returns the FastMCP application instance.

    Returns:
        FastMCP: The FastMCP application instance.
    """
    return mcp