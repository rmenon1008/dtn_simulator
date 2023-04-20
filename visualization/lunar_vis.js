let PIXEL_MULTIPLIER = 3;
let SCALE = 0.8;

let showRanges = true;
let historyFade = false;
let showDetectionLines = false;
let showTargetLocations = true;

const LunarVis = function (maxSimX, maxSimY) {
  const elements = document.getElementById("elements");
  let width = elements.getBoundingClientRect().width;

  // Create a canvas element with the correct aspect ratio
  const canvasContainer = document.createElement('div');
  const canvas = document.createElement('canvas');
  const context = canvas.getContext("2d");

  canvas.width = width * PIXEL_MULTIPLIER;
  canvas.height = width * maxSimY / maxSimX * PIXEL_MULTIPLIER;
  canvas.style.width = width + "px";
  canvas.style.height = width * maxSimY / maxSimX + "px";

  let scaleFactor = canvas.width / maxSimX;

  canvasContainer.appendChild(canvas);
  elements.appendChild(canvasContainer);

  canvasContainer.style.position = "relative";

  window.addEventListener("resize", () => {
    width = elements.getBoundingClientRect().width;
    canvas.width = width * PIXEL_MULTIPLIER;
    canvas.height = width * maxSimY / maxSimX * PIXEL_MULTIPLIER;
    canvas.style.width = width + "px";
    canvas.style.height = width * maxSimY / maxSimX + "px";
    scaleFactor = canvas.width / maxSimX;
    this.rerender();
  });


  // Scales simulation coordinates to canvas coordinates
  const scale = (mag) => { return Math.floor(mag * scaleFactor) };


  // Draws a circle or square at the given coordinates
  const drawShape = (x, y, size, color, shape = "circle", centerDot = false, gradientEdgeColor = null, outline = false) => {
    context.beginPath();
    if (gradientEdgeColor) {
      size = size * 1.1;
      const grad = context.createRadialGradient(scale(x), scale(y), 0, scale(x), scale(y), scale(size));
      grad.addColorStop(0, color);
      grad.addColorStop(0.9, color);
      grad.addColorStop(1, gradientEdgeColor);
      context.fillStyle = grad;
    } else {
      context.fillStyle = color;
    }

    if (outline) {
      context.arc(scale(x), scale(y), scale(size * 1.25), 0, 2 * Math.PI);
      context.strokeStyle = "black";
      context.stroke();
    }
    if (shape === "circle") {
      context.arc(scale(x), scale(y), scale(size), 0, 2 * Math.PI);
      context.fill();
    } else if (shape === "square") {
      context.rect(scale(x - size * 1.7 / 2), scale(y - size * 1.7 / 2), scale(size * 1.7), scale(size * 1.7));
      context.fill();
    } else if (shape === "X") {
      context.moveTo(scale(x - size * 1.7 / 2), scale(y - size * 1.7 / 2));
      context.lineTo(scale(x + size * 1.7 / 2), scale(y + size * 1.7 / 2));
      context.moveTo(scale(x - size * 1.7 / 2), scale(y + size * 1.7 / 2));
      context.lineTo(scale(x + size * 1.7 / 2), scale(y - size * 1.7 / 2));
      context.lineWidth = 3 * PIXEL_MULTIPLIER * SCALE;
      context.strokeStyle = color;
      context.stroke();
    }

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
    if (rssi === null) {
      return "#777";
    }
    const val = Math.exp(-0.0921034 * rssi) / maxRange;
    let red = Math.round(255 * val);
    let green = Math.round(255 * (1 - val));
    return `rgba(${red}, ${green}, 0, ${opacity})`;
  };

  // Get the max rssi from a neighborhood
  const getMaxRssi = (neighborhood) => {
    let maxRssi = -999;
    neighborhood.forEach((node) => {
      if (node.rssi > maxRssi) {
        maxRssi = node.rssi;
      }
    });
    return maxRssi == -999 ? null : maxRssi;
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

    const nodeInfo = node;
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
    }, (key, value) => {
      showRanges = value;
      this.rerender();
    })
  )

  visOptions.append(
    addBooleanInput("node_history", {
      name: "Fade node history",
      value: historyFade
    }, (key, value) => {
      historyFade = value;
      this.rerender();
    })
  )

  visOptions.append(
    addBooleanInput("radio_lines", {
      name: "Show radio lines",
      value: showDetectionLines
    }, (key, value) => {
      showDetectionLines = value;
      this.rerender();
    })
  )

  visOptions.append(
    addBooleanInput("show_target_locations", {
      name: "Show target locations",
      value: showTargetLocations
    }, (key, value) => {
      showTargetLocations = value;
      this.rerender();
    })
  )


  // Clears the canvas
  this.reset = function () {
    context.clearRect(0, 0, canvas.width, canvas.height);
  }


  // Renders the current simulation state
  // Called every frame
  this.lastModelState = null;
  this.render = function (modelState) {
    this.lastModelState = modelState;
    console.log(modelState);
    context.clearRect(0, 0, canvas.width, canvas.height);

    const nodes = modelState.nodes;
    const data_drops = modelState.data_drops;

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
            color = colorFromSignal(getMaxRssi(entry.radio.neighborhood), node.radio.estimated_detection_range, transparency);
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
        if (node.radio.estimated_detection_range) {
          drawShape(node.pos[0], node.pos[1], node.radio.estimated_detection_range, "rgba(0, 0, 255, 0.07)", "circle", false, "rgba(0, 0, 255, 0.0)");
        }
      });
      nodes.forEach(node => {
        if (node.radio.estimated_connection_range) {
          drawShape(node.pos[0], node.pos[1], node.radio.estimated_connection_range, "rgba(0, 255, 0, 0.15)", "circle", false, "rgba(0, 255, 0, 0.0)");
        }
      });
    }

    // Draw lines between nodes that have an RSSI
    nodes.forEach(node => {
      if (node.radio.neighborhood) {
        node.radio.neighborhood.forEach(neighbor => {
          if (neighbor.connected || showDetectionLines) {
            const otherNode = getNode(neighbor.id);
            drawLine(node.pos[0], node.pos[1], otherNode.pos[0], otherNode.pos[1], colorFromSignal(neighbor.rssi, node.radio.estimated_detection_range));
          }
        });
      }
    });

    // Draw all the nodes on top
    nodes.forEach(node => {
      let hasData = false;
      if (node.curr_num_stored_payloads && node.curr_num_stored_payloads > 0) {
        hasData = true;
      } else if (node.routing_protocol && node.routing_protocol.curr_num_stored_bundles > 0) {
        hasData = true;
      }
      let hasDataToDeliverToClientDirectly = false;
      if (node.curr_num_payloads_received_for_client && node.curr_num_payloads_received_for_client > 0) {
        hasDataToDeliverToClientDirectly = true;
      }
      const sigcolor = colorFromSignal(getMaxRssi(node.radio.neighborhood), node.radio.estimated_detection_range);
      drawShape(x=node.pos[0], y=node.pos[1], size=8 * SCALE, color=sigcolor, shape="circle", centerDot=hasData, gradientEdgeColor=null, outline=hasDataToDeliverToClientDirectly);
      addTooltip(node);
    });

    // Draw data drops
    data_drops.forEach(drop => {
      drawShape(drop.pos[0], drop.pos[1], 5 * SCALE, "rgba(255, 0, 0, 0.5)", "square", false);
    });

    // // Draw nodes target locations
    // if (showTargetLocations) {
    //   nodes.forEach(node => {
    //     if (node.target_location) {
    //       drawShape(node.target_location[0], node.target_location[1], 5 * SCALE, "rgba(0, 0, 255, 0.5)", "X");
    //     }
    //   });
    // }
  }

  this.rerender = function () {
    if (this.lastModelState) {
      console.log("rerendering");
      this.render(this.lastModelState);
    }
  }

};
