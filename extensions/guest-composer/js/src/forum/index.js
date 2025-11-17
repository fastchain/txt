// /flarum/app # composer config repositories.guest-composer path /extensions/guest-composer
// /flarum/app # composer require yours/guest-composer:*
// /flarum/app # composer config minimum-stability dev
// /flarum/app # composer config prefer-stable true
// /flarum/app # composer require yours/guest-composer:*



import app from 'flarum/forum/app';
import { extend } from 'flarum/common/extend';
import IndexPage from 'flarum/forum/components/IndexPage';
import DiscussionPage from 'flarum/forum/components/DiscussionPage';
import Button from 'flarum/common/components/Button';
import DiscussionComposer from 'flarum/forum/components/DiscussionComposer';
import ReplyComposer from 'flarum/forum/components/ReplyComposer';

// (опционально) аккуратно попытаемся подключить выбор тегов, если flarum/tags установлен
let TagSelectionModal = null;
try {
  // @ts-ignore
  TagSelectionModal = require('flarum/tags/components/TagSelectionModal').default;
} catch (e) {
  TagSelectionModal = null;
}

function openReplyComposer(discussion) {
  app.composer.load(ReplyComposer, { discussion });
  app.composer.show();
}

function openNewDiscussionComposer({ withTags = true } = {}) {
  app.composer.load(DiscussionComposer, {}); // <-- именно так: класс + attrs
  app.composer.show();

  if (withTags && TagSelectionModal) {
    app.modal.show(TagSelectionModal, {
      selectedTags: [],
      onsubmit: tags => {
        // Flarum сам подхватит tags из модалки при публикации
        // (если нужно, можно сохранить в app.composer.fields, но обычно не требуется)
      },
    });
  }
}

//Show composer for guests
app.initializers.add('anon-guest-composer', () => {


  const AUTO_TAG_ID = '2'; // ← change this to your tag id

  const origSubmit = DiscussionComposer.prototype.onsubmit;
  DiscussionComposer.prototype.onsubmit = function (e) {

    const data = this.data();
    data.relationships = data.relationships || {};
    data.relationships.tags = { data: [{ type: 'tags', id: AUTO_TAG_ID }] };

    this.data = () => data;

    return origSubmit.call(this, e);
  };

  //
  const isGuest = !app.session?.user;
  if (!isGuest) return;

  // Разрешим фронту показывать кнопки
  try {
    if (app.forum?.data?.attributes) {
      app.forum.data.attributes.canStartDiscussion = true;
    }
  } catch (_) {}

  // Подстраховка на темы, скрывающие кнопки
  const style = document.createElement('style');
  style.textContent = `
    .Button--newDiscussion,
    .item-reply .Button { display:inline-flex !important; opacity:1 !important; pointer-events:auto !important; }
  `;
  document.head.appendChild(style);

  // Главная: добавляем кнопку "New Discussion"
  extend(IndexPage.prototype, 'actionItems', function (items) {
    items.add(
      'anonGuestNewDiscussion',
      Button.component(
        {
          className: 'Button Button--primary',
          onclick: () => openNewDiscussionComposer({ withTags: true }),
        },
        app.translator.trans('core.forum.index.start_discussion_button')
      ),
      0
    );
  });

  // Страница обсуждения: добавляем кнопку "Reply"
  extend(DiscussionPage.prototype, 'actionItems', function (items) {
    items.add(
      'anonGuestReply',
      Button.component(
        {
          className: 'Button Button--primary',
          onclick: () => openReplyComposer(this.discussion),
        },
        app.translator.trans('core.forum.discussion.reply_button')
      ),
      0
    );
  });

  // Перехват клика по уже существующим Reply (если их рендерит тема/расширения)
  // document.addEventListener(
  //   'click',
  //   (e) => {
  //     if (app.session?.user) return; // не мешаем залогиненным
  //     const btn = e.target && e.target.closest('.item-reply .Button, [data-item-id="reply"] .Button');
  //     if (!btn) return;
  //     e.preventDefault();
  //     e.stopImmediatePropagation();
  //     const current = app.current?.get?.('discussion');
  //     if (current) openReplyComposer(current);
  //   },
  //   true
  // );
});
