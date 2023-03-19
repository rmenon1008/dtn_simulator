const WIDTH = 1250;
const PIXEL_MULTIPLIER = 3;

const SCALE = 1;
const RANGES_ONLY_ON_FIXED_AGENTS = true;

const LunarVis = function(maxSimX, maxSimY) {
  // Create a canvas element with the correct aspect ratio
  const canvas = document.createElement('canvas');
  const context = canvas.getContext("2d");
  canvas.width = WIDTH * PIXEL_MULTIPLIER;
  canvas.height = WIDTH * maxSimY / maxSimX * PIXEL_MULTIPLIER;
  canvas.style.width = WIDTH + "px";
  canvas.style.height = WIDTH * maxSimY / maxSimX + "px";
  const scaleFactor = canvas.width / maxSimX;

  // Add the canvas to the DOM
  const elements = document.getElementById("elements");
  elements.appendChild(canvas);

  // Functions to scale  simulation coordinates to the canvas
  const scale = (mag) => { return mag * scaleFactor };

  const drawShape = (x, y, size, color, shape = "circle", outline = false) => {
    context.beginPath();
    if (shape === "circle") {
      context.arc(scale(x), scale(y), scale(size), 0, 2 * Math.PI);
    } else if (shape === "square") {
      size = size * 1.7;
      context.rect(scale(x - size / 2), scale(y - size / 2), scale(size), scale(size));
    }

    if (outline) {
      context.lineWidth = 4 * PIXEL_MULTIPLIER * SCALE;
      context.strokeStyle = "black";
      context.stroke();
    }

    context.fillStyle = color;
    context.fill();
  };

  const drawLine = (x1, y1, x2, y2, color) => {
    context.beginPath();
    context.moveTo(scale(x1), scale(y1));
    context.lineTo(scale(x2), scale(y2));
    context.strokeStyle = color;
    context.stroke();
  };

  const colorFromSignal = (rssi, maxRange = 300) => {
    // rssi is a value in dBm
    const val = Math.exp(-0.0921034 * rssi) / maxRange;
    const red = Math.round(255 * val);
    const green = Math.round(255 * (1 - val));
    return `rgb(${red}, ${green}, 0)`;
  };

  this.render = function(nodes) {
    console.log(nodes);
    context.clearRect(0, 0, canvas.width, canvas.height);

    const getNode = (id) => {
      return nodes.find(node => node.id === id);
    };

    // Draw lines between historical data points
    nodes.forEach(node => {
      if (node.history) {
        for (let i = 0; i < node.history.length - 1; i++) {
          const entry = node.history[i];
          const nextEntry = node.history[i + 1];
          drawLine(entry.pos[0], entry.pos[1], nextEntry.pos[0], nextEntry.pos[1], "rgba(0, 0, 0, 0.1)");
        }
      }
    });

    // Draw the historical RSSI values
    nodes.forEach(node => {
      if (node.history) {
        for (let i = 0; i < node.history.length - 1; i++) {
          const entry = node.history[i];
          let color = "rgba(0, 0, 0, 0.1)";
          if (entry.radio.neighborhood) {
            color = colorFromSignal(entry.radio.best_rssi, node.radio.detection_range);
          }
          drawShape(entry.pos[0], entry.pos[1], 3 * SCALE, color, "circle");
        }
      }
    });

    // Draw the detection and connection ranges as transparent circles
    nodes.forEach(node => {
      if (node.radio.detection_range && (!RANGES_ONLY_ON_FIXED_AGENTS || node.type === "fixed")) {
        drawShape(node.pos[0], node.pos[1], node.radio.detection_range, "rgba(0, 0, 255, 0.04)");
      }
    });
    nodes.forEach(node => {
      if (node.radio.connection_range && (!RANGES_ONLY_ON_FIXED_AGENTS || node.type === "fixed")) {
        drawShape(node.pos[0], node.pos[1], node.radio.connection_range, "rgba(0, 255, 0, 0.15)");
      }
    });

    // Draw lines between nodes that have an RSSI
    // TODO: Avoid drawing lines twice
    nodes.forEach(node => {
      if (node.radio.neighborhood) {
        node.radio.neighborhood.forEach(neighbor => {
          if (neighbor.connected) {
            const otherNode = getNode(neighbor.id);
            drawLine(node.pos[0], node.pos[1], otherNode.pos[0], otherNode.pos[1], colorFromSignal(neighbor.rssi, node.radio.detection_range));
          }
        });
      }
    });

    // Draw all the nodes on top
    nodes.forEach(node => {
      const color = colorFromSignal(node.radio.best_rssi, node.radio.detection_range);
      drawShape(node.pos[0], node.pos[1], 5 * SCALE, color, (node.type === "mobile" ? "circle" : "square"), node.hdtn.has_data);
    });
  };

  this.reset = function() {
    // Clear the canvas
    context.clearRect(0, 0, canvas.width, canvas.height);
  }
};
