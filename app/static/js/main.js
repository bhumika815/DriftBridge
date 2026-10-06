/* DriftBridge — shared JS */

document.addEventListener('DOMContentLoaded', function () {

    /* =====================================================
       MOBILE NAV TOGGLE
       ===================================================== */

    var toggle = document.querySelector('.navbar-toggle');
    var links = document.querySelector('.navbar-links');

    if (toggle && links) {

        toggle.addEventListener('click', function () {

            links.classList.toggle('open');

        });

    }


    /* =====================================================
       AUTO-DISMISS FLASH MESSAGES
       ===================================================== */

    document.querySelectorAll('.flash').forEach(function (el) {

        setTimeout(function () {

            el.style.transition = 'opacity 0.5s';
            el.style.opacity = '0';

            setTimeout(function () {

                el.remove();

            }, 500);

        }, 5000);

    });

});