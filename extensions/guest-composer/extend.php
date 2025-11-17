<?php

use Flarum\Extend;

return [
    // Подключаем собранный фронтенд-бандл
    (new Extend\Frontend('forum'))
        ->js(__DIR__.'/js/dist/forum.js'),
];
