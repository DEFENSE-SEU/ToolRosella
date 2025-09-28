#!/usr/bin/env python3
"""
Visualize the P-wave input data to show what the earthquake waveform looks like
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import signal as sp_signal

def generate_p_wave_data(duration=30, sampling_rate=100, magnitude=5.2):
    """Generate the same P-wave data as used in the LLM test"""
    t = np.linspace(0, duration, int(duration * sampling_rate))

    # Background noise (realistic seismic noise level)
    noise = np.random.normal(0, 0.001, len(t))

    # P-wave arrival parameters
    p_arrival_time = 8.5  # seconds
    p_mask = t >= p_arrival_time

    # P-wave signal characteristics
    p_wave = np.zeros_like(t)
    p_wave[p_mask] = (magnitude/5.0) * 0.01 * \
        (np.sin(2*np.pi*8*(t[p_mask]-p_arrival_time)) +
         0.3*np.sin(2*np.pi*12*(t[p_mask]-p_arrival_time))) * \
        np.exp(-0.1*(t[p_mask]-p_arrival_time))

    # Add coda waves (scattered energy after main arrival)
    coda_start = p_arrival_time + 5
    coda_mask = t >= coda_start
    p_wave[coda_mask] += (magnitude/5.0) * 0.003 * \
        np.random.normal(0, 1, np.sum(coda_mask)) * \
        np.exp(-0.05*(t[coda_mask]-coda_start))

    # Combine signal with noise
    signal = noise + p_wave

    # Apply instrument response (high-pass filter)
    b, a = sp_signal.butter(2, 0.5/(sampling_rate/2), btype='high')
    signal = sp_signal.filtfilt(b, a, signal)

    return t, signal, p_arrival_time

def create_pwave_visualization():
    """Create comprehensive P-wave visualization"""
    print("🌊 Generating P-wave visualization...")

    # Generate P-wave data
    t, signal, p_arrival = generate_p_wave_data()

    # Create figure with multiple subplots
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    fig.suptitle('P-wave Input Data Analysis\nMagnitude 5.2 Earthquake - San Francisco Bay Area',
                 fontsize=14, fontweight='bold')

    # 1. Full waveform
    axes[0].plot(t, signal, 'b-', linewidth=0.8, alpha=0.8)
    axes[0].axvline(x=p_arrival, color='r', linestyle='--', linewidth=2,
                   label=f'P-wave arrival ({p_arrival}s)')
    axes[0].set_ylabel('Amplitude')
    axes[0].set_title('Complete 30-second Seismogram')
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    # Add annotations for different phases
    axes[0].annotate('Background\nNoise', xy=(3, 0.005), xytext=(2, 0.008),
                    arrowprops=dict(arrowstyle='->', color='gray'),
                    fontsize=10, ha='center')
    axes[0].annotate('P-wave\nArrival', xy=(p_arrival, 0.01), xytext=(p_arrival+2, 0.012),
                    arrowprops=dict(arrowstyle='->', color='red'),
                    fontsize=10, ha='center')
    axes[0].annotate('Coda\nWaves', xy=(15, 0.003), xytext=(18, 0.006),
                    arrowprops=dict(arrowstyle='->', color='green'),
                    fontsize=10, ha='center')

    # 2. Zoomed view around P-wave arrival
    zoom_start = p_arrival - 2
    zoom_end = p_arrival + 8
    zoom_mask = (t >= zoom_start) & (t <= zoom_end)

    axes[1].plot(t[zoom_mask], signal[zoom_mask], 'b-', linewidth=1.2)
    axes[1].axvline(x=p_arrival, color='r', linestyle='--', linewidth=2)
    axes[1].set_ylabel('Amplitude')
    axes[1].set_title('Zoomed View: P-wave Arrival (6.5-16.5 seconds)')
    axes[1].grid(True, alpha=0.3)

    # Highlight the exponential decay
    decay_mask = (t >= p_arrival) & (t <= p_arrival + 5)
    if np.any(decay_mask):
        envelope = np.abs(signal[decay_mask])
        axes[1].plot(t[decay_mask], envelope, 'r--', alpha=0.7, linewidth=1.5,
                    label='Amplitude envelope')
        axes[1].plot(t[decay_mask], -envelope, 'r--', alpha=0.7, linewidth=1.5)
        axes[1].legend()

    # 3. Frequency spectrum
    from scipy.fft import fft, fftfreq

    # Focus on P-wave portion for frequency analysis
    p_wave_mask = (t >= p_arrival) & (t <= p_arrival + 10)
    p_wave_data = signal[p_wave_mask]

    # Compute FFT
    fft_data = fft(p_wave_data)
    freqs = fftfreq(len(p_wave_data), 1/100)  # 100 Hz sampling rate

    # Only plot positive frequencies up to 25 Hz
    pos_freq_mask = (freqs > 0) & (freqs <= 25)

    axes[2].plot(freqs[pos_freq_mask], np.abs(fft_data[pos_freq_mask]), 'g-', linewidth=1.5)
    axes[2].axvline(x=8, color='orange', linestyle=':', linewidth=2, label='Primary freq (8 Hz)')
    axes[2].axvline(x=12, color='purple', linestyle=':', linewidth=2, label='Secondary freq (12 Hz)')
    axes[2].set_xlabel('Frequency (Hz)')
    axes[2].set_ylabel('Amplitude Spectrum')
    axes[2].set_title('Frequency Content of P-wave')
    axes[2].grid(True, alpha=0.3)
    axes[2].legend()

    plt.tight_layout()

    # Save the visualization
    output_file = '/Users/yuanxujie/Downloads/Easy-Tool/p_wave_visualization.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"📊 P-wave visualization saved: {output_file}")

    # Display key characteristics
    print("\n📈 P-wave Data Characteristics:")
    print(f"   🕐 Total duration: 30 seconds")
    print(f"   📊 Sampling rate: 100 Hz (3000 data points)")
    print(f"   ⚡ P-wave arrival: {p_arrival} seconds")
    print(f"   📏 Max amplitude: {np.max(np.abs(signal)):.6f}")
    print(f"   🎵 Dominant frequencies: 8 Hz and 12 Hz")
    print(f"   📉 Exponential decay: exp(-0.1*t)")
    print(f"   🌊 Background noise level: ±0.001")

    # Show amplitude ranges
    noise_only = signal[t < p_arrival]
    signal_portion = signal[t >= p_arrival]

    print(f"\n📊 Amplitude Analysis:")
    print(f"   🔇 Background noise RMS: {np.sqrt(np.mean(noise_only**2)):.6f}")
    print(f"   📢 Signal+noise RMS: {np.sqrt(np.mean(signal_portion**2)):.6f}")
    print(f"   📈 Signal-to-noise ratio: {np.sqrt(np.mean(signal_portion**2))/np.sqrt(np.mean(noise_only**2)):.1f}")

    return output_file

if __name__ == "__main__":
    visualization_file = create_pwave_visualization()
    print(f"\n✅ P-wave input data visualization complete!")
    print(f"📁 View the visualization: {visualization_file}")