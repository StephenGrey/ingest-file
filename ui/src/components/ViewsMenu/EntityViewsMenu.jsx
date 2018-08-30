import React from 'react';
import { withRouter } from 'react-router';
import { injectIntl, defineMessages } from 'react-intl';
import { connect } from "react-redux";

import { queryEntitySimilar } from 'src/queries';
import { fetchEntityReferences } from "src/actions";
import { selectEntityReferences, selectEntityTags, selectMetadata, selectEntitiesResult } from "src/selectors";
import ViewItem from "src/components/ViewsMenu/ViewItem";

import './ViewsMenu.css';

const messages = defineMessages({
  info: {
    id: 'entity.mode.info',
    defaultMessage: 'Base information',
  },
  tags: {
    id: 'entity.mode.tags',
    defaultMessage: 'Tags',
  },
  similar: {
    id: 'entity.mode.similar',
    defaultMessage: 'Similar',
  }
});

class EntityViewsMenu extends React.Component {
  render() {
    const {intl, isPreview, activeMode, entity} = this.props;
    const { references, tags, similar } = this.props;
    const { metadata } = this.props;
    const { schemata } = metadata;
    const className = !isPreview ? 'ViewsMenu FullPage' : 'ViewsMenu';

    return (
      <div className={className}>
        {isPreview && (
          <ViewItem mode='info' activeMode={activeMode} isPreview={isPreview}
            message={intl.formatMessage(messages.info)}
            icon='pt-icon-info-sign' />
        )}
        {references.results !== undefined && references.results.map((ref) => (
          <ViewItem key={ref.property.qname} 
                    mode={ref.property.qname}
                    activeMode={activeMode}
                    isPreview={isPreview}
                    message={ref.property.reverse}
                    href={'/entities/' + entity.id + '#mode=' + ref.property.qname}
                    icon={schemata[ref.schema].icon} />
        ))}
        <ViewItem mode='similar' activeMode={activeMode} isPreview={isPreview}
          disabled={similar.total === 0}
          message={intl.formatMessage(messages.similar)}
          href={'/entities/' + entity.id + '/similar'}
          icon='fa-repeat' />
        <ViewItem mode='tags' activeMode={activeMode} isPreview={isPreview}
          disabled={tags.total === 0}
          message={intl.formatMessage(messages.tags)}
          href={'/entities/' + entity.id + '/tags'}
          icon='fa-tags' />
      </div>
    );
  }
}

const mapStateToProps = (state, ownProps) => {
  const { entity, location } = ownProps;
  return {
    references: selectEntityReferences(state, entity.id),
    metadata: selectMetadata(state),
    tags: selectEntityTags(state, entity.id),
    similar: selectEntitiesResult(state, queryEntitySimilar(location, entity.id))
  };
};

EntityViewsMenu = connect(mapStateToProps, { fetchEntityReferences })(EntityViewsMenu);
EntityViewsMenu = injectIntl(EntityViewsMenu);
EntityViewsMenu = withRouter(EntityViewsMenu);
export default EntityViewsMenu;