# styled-components-killer
Replaces styled components with modular css (For those that care about a performant website!)

This script is configured to transform any styled components written in a form to
:
```javascript
const FormCol = styled.div`
    width: 48%;
    .inputText {
        text-align: left;
        margin-bottom: 0;
    }
    @media (max-width: 999px) {
        width: 100%;
    }
`;
```

Into the respective module scss, and javscript file, in the folder where the component was found

`styleManual.module.scss`
```scss
.formCol {
    width: 48%;
    .inputText {
        text-align: left;
        margin-bottom: 0;
    }
    @media (max-width: 999px) {
        width: 100%;
    }
  }
```

`index.js`
```javascript
import styleManual from './styleManual.module.scss';

const FormCol = (props) => {
                  const {children} = props;
                  return (<div {...props} className={styleManual.formCol}>
                      {children}
                  </div>);
              };
```

Use:
`python3 styled_components_killer.py --dir=<directory> --verbose=<true|false> --dry_run=<true|false>
