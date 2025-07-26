import React, { useRef, useEffect } from "react";
import CytoscapeComponent from "react-cytoscapejs";

function CytoscapeGraph({
  elements,
  style = { width: "600px", height: "400px" },
  layout = {
    name: "cose",
    padding: 10,
    animate: true,
    animationDuration: 1000,
  },
}) {
  const cyRef = useRef(null);

  useEffect(() => {
    console.log("Graph elements:", elements);
    const cy = cyRef.current;
    if (cy && !cy.destroyed) {
      cy.layout(layout).run();
    }
  }, [elements, layout]);

  return (
    <CytoscapeComponent
      elements={elements}
      style={style}
      layout={layout}
      stylesheet={[
        {
          selector: "node[label]",
          style: {
            label: "data(label)", // only show label if present
            "background-color": "#003366",
            color: "#eee",
            "text-valign": "center",
            "text-halign": "center",
            "font-size": "10px",
            width: "30px",
            height: "30px",
          },
        },
        {
          selector: "node:not([label])",
          style: {
            label: "", // no label if none provided
            "background-color": "#003366",
            width: "30px",
            height: "30px",
          },
        },
        {
          selector: "edge",
          style: {
            width: 2,
            "line-color": "#444",
            "target-arrow-color": "#444",
            "target-arrow-shape": "triangle",
            "curve-style": "bezier",
          },
        },
      ]}
      cy={(cy) => {
        cyRef.current = cy;
      }}
    />
  );
}

export default CytoscapeGraph;
