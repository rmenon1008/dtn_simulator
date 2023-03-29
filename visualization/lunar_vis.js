let PIXEL_MULTIPLIER = 3;
let SCALE = 1;

let showRanges = true;
let historyFade = true;
let showDetectionLines = true;

const LunarVis = function (maxSimX, maxSimY) {
  const elements = document.getElementById("elements");
  const width = elements.getBoundingClientRect().width;

  // Create a canvas element with the correct aspect ratio
  const canvasContainer = document.createElement('div');
  const canvas = document.createElement('canvas');
  const context = canvas.getContext("2d");

  canvas.width = width * PIXEL_MULTIPLIER;
  canvas.height = width * maxSimY / maxSimX * PIXEL_MULTIPLIER;
  canvas.style.width = width + "px";
  canvas.style.height = width * maxSimY / maxSimX + "px";

  const scaleFactor = canvas.width / maxSimX;

  canvasContainer.appendChild(canvas);
  elements.appendChild(canvasContainer);

  canvasContainer.style.position = "relative";


  // Scales simulation coordinates to canvas coordinates
  const scale = (mag) => { return Math.floor(mag * scaleFactor) };


  // Draws a circle or square at the given coordinates
  const drawShape = (x, y, size, color, shape = "circle", centerDot = false) => {
    context.beginPath();
    if (shape === "circle") {
      context.arc(scale(x), scale(y), scale(size), 0, 2 * Math.PI);
    } else if (shape === "square") {
      context.rect(scale(x - size * 1.7 / 2), scale(y - size * 1.7 / 2), scale(size * 1.7), scale(size * 1.7));
    }

    context.fillStyle = color;
    context.fill();

    if (centerDot) {
      context.beginPath();
      context.arc(scale(x), scale(y), scale(size / 2), 0, 2 * Math.PI);
      context.fillStyle = "black";
      context.fill();
    }
  };


  // Draws a line between two points
  const drawLine = (x1, y1, x2, y2, color) => {
    context.lineWidth = 3 * PIXEL_MULTIPLIER * SCALE;
    context.beginPath();
    context.moveTo(scale(x1), scale(y1));
    context.lineTo(scale(x2), scale(y2));
    context.strokeStyle = color;
    context.stroke();
  };


  // Determines the color for an RSSI value
  const colorFromSignal = (rssi, maxRange = 300, opacity = 1.0) => {
    const val = Math.exp(-0.0921034 * rssi) / maxRange;
    let red = Math.round(255 * val);
    let green = Math.round(255 * (1 - val));
    return `rgba(${red}, ${green}, 0, ${opacity})`;
  };

  // Adds a hoverable tooltip for a node
  const addTooltip = (node) => {
    // Find the tooltip if it already exists
    let nodeElem = document.getElementById("node-" + node.id);
    if (nodeElem) {
      nodeElem.remove();
    }

    // Create a new tooltip
    tooltip = document.createElement("div");
    nodeElem = document.createElement("div");

    tooltip.className = "tooltip";
    tooltip.style.left = scale(node.pos[0]) / 3 + "px";
    tooltip.style.top = scale(node.pos[1]) / 3 + "px";

    nodeElem.className = "node";
    nodeElem.style.left = scale(node.pos[0]) / 3 - 15 + "px";
    nodeElem.style.top = scale(node.pos[1]) / 3 - 15 + "px";
    nodeElem.id = "node-" + node.id;

    const nodeInfo = {
      "hdtn": node.hdtn,
      "radio": node.radio,
      "history": node.history,
    };

    const formatter = new JSONFormatter(nodeInfo, 1, {
      hoverPreviewEnabled: false,
      hoverPreviewArrayCount: 100,
      hoverPreviewFieldCount: 5,
      theme: 'dark',
      animateOpen: true,
      animateClose: false,
      useToJSON: true,
      maxArrayItems: 100,
      exposePath: false
    });

    tooltip.innerHTML = `<h3>Rover ${node.id}</h3>`;
    tooltip.appendChild(formatter.render());

    // Add the tooltip to the DOM
    nodeElem.appendChild(tooltip);
    canvasContainer.appendChild(nodeElem);
  };

  // Adds visualization options to the DOM
  visOptions.append(
    addBooleanInput("node_ranges", {
      name: "Show node ranges",
      value: showRanges
    }, (key, value) => { showRanges = value; })
  )

  visOptions.append(
    addBooleanInput("node_history", {
      name: "Fade node history",
      value: historyFade
    }, (key, value) => { historyFade = value; })
  )

  visOptions.append(
    addBooleanInput("radio_lines", {
      name: "Show radio lines",
      value: showDetectionLines
    }, (key, value) => { showDetectionLines = value; })
  )


  // Clears the canvas
  this.reset = function () {
    context.clearRect(0, 0, canvas.width, canvas.height);
  }


  // Renders the current simulation state
  // Called every frame
  this.render = function (nodes) {
    console.log(nodes);
    context.clearRect(0, 0, canvas.width, canvas.height);

    const getNode = (id) => {
      return nodes.find(node => node.id === id);
    };

    // Draw the historical RSSI values
    nodes.forEach(node => {
      var transparency = 1;
      if (node.history.reverse()) {
        for (let i = 0; i < node.history.length - 1; i++) {
          const entry = node.history[i];
          let color = "rgba(0, 0, 0, 0.1)";
          if (entry.radio.neighborhood) {
            color = colorFromSignal(entry.radio.best_rssi, node.radio.detection_range, transparency);
            if (historyFade) {
              transparency = Math.max(0, transparency * 0.995 - 0.001);
            }
          }
          drawShape(entry.pos[0], entry.pos[1], 3 * SCALE, color, "circle");
        }
      }
    });

    // Draw the detection and connection ranges as transparent circles
    if (showRanges) {
      nodes.forEach(node => {
        if (node.radio.detection_range) {
          drawShape(node.pos[0], node.pos[1], node.radio.detection_range, "rgba(0, 0, 255, 0.04)");
        }
      });
      nodes.forEach(node => {
        if (node.radio.connection_range) {
          drawShape(node.pos[0], node.pos[1], node.radio.connection_range, "rgba(0, 255, 0, 0.15)");
        }
      });
    }

    // Draw lines between nodes that have an RSSI
    nodes.forEach(node => {
      if (node.radio.neighborhood) {
        node.radio.neighborhood.forEach(neighbor => {
          if (neighbor.connected || showDetectionLines) {
            const otherNode = getNode(neighbor.id);
            drawLine(node.pos[0], node.pos[1], otherNode.pos[0], otherNode.pos[1], colorFromSignal(neighbor.rssi, node.radio.detection_range));
          }
        });
      }
    });

    // Draw all the nodes on top
    nodes.forEach(node => {
      const color = colorFromSignal(node.radio.best_rssi, node.radio.detection_range);
      drawShape(node.pos[0], node.pos[1], 8 * SCALE, color, (node.type === "mobile" ? "circle" : "square"), node.hdtn.has_data);
      addTooltip(node);
    });

  };
};
