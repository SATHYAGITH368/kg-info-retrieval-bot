// src/components/EntityTree.js
import '@ebi-ols/ols4-widgets/treestyles.css';
import { useEffect, useRef } from 'react';
import { createEntityTree } from '@ebi-ols/ols4-widgets/ols4_widgets';

function EntityTree({ ontologyId = 'chebi', specifiedRootIri = null }) {
  const divRef = useRef();

  useEffect(() => {
    if (divRef.current) {
      createEntityTree(
        {
          ontologyId,
          specifiedRootIri,
          apiUrl: 'https://www.ebi.ac.uk/ols4/',
        },
        divRef.current
      );
    }
  }, [ontologyId, specifiedRootIri]);

  return <div ref={divRef} style={{ maxHeight: '600px', overflowY: 'auto' }} />;
}

export default EntityTree;
