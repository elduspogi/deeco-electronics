/*!
* Start Bootstrap - Creative v7.0.7 (https://startbootstrap.com/theme/creative)
* Copyright 2013-2023 Start Bootstrap
* Licensed under MIT (https://github.com/StartBootstrap/startbootstrap-creative/blob/master/LICENSE)
*/
//
// Scripts
// 

window.addEventListener('DOMContentLoaded', event => {

    // Navbar shrink function
    var navbarShrink = function () {
        const navbarCollapsible = document.body.querySelector('#mainNav');
        if (!navbarCollapsible) {
            return;
        }
        if (window.scrollY === 0) {
            navbarCollapsible.classList.remove('navbar-shrink')
        } else {
            navbarCollapsible.classList.add('navbar-shrink')
        }

    };

    // Shrink the navbar 
    navbarShrink();

    // Shrink the navbar when page is scrolled
    document.addEventListener('scroll', navbarShrink);

    // Activate Bootstrap scrollspy on the main nav element
    const mainNav = document.body.querySelector('#mainNav');
    if (mainNav) {
        new bootstrap.ScrollSpy(document.body, {
            target: '#mainNav',
            rootMargin: '0px 0px -40%',
        });
    };

    // Collapse responsive navbar when toggler is visible
    const navbarToggler = document.body.querySelector('.navbar-toggler');
    const responsiveNavItems = [].slice.call(
        document.querySelectorAll('#navbarResponsive .nav-link')
    );
    responsiveNavItems.map(function (responsiveNavItem) {
        responsiveNavItem.addEventListener('click', () => {
            if (window.getComputedStyle(navbarToggler).display !== 'none') {
                navbarToggler.click();
            }
        });
    });

    // Activate SimpleLightbox plugin for portfolio items
    // new SimpleLightbox({
    //     elements: '#portfolio a.portfolio-box'
    // });

});

// Initialize AOS
function aos() {
    AOS.init({
        duration: 1000,
        easing: "ease-in-out",
        once: true,
        mirror: false
    });
}

window.addEventListener('load', () => {
    aos();
});

// Back To Top Button
const goTopBtn = document.querySelector('.back-to-top');

window.addEventListener('scroll', checkHeight)

function checkHeight() {
    if(window.scrollY > 50) {
        goTopBtn.classList.add('show');
        goTopBtn.classList.remove('hide');
    } else {
        goTopBtn.classList.remove('show')
        goTopBtn.classList.add('hide');
    }
}

goTopBtn.addEventListener('click', () => {
    window.scrollTo({
        top: 0,
        behavior: "smooth"
    })
})

document.getElementById('navbar-toggler').addEventListener('click', function() {
    const icon = document.getElementById('navbar-icon');
    if (icon.classList.contains('navbar-toggler-icon')) {
        icon.classList.remove('navbar-toggler-icon');
        icon.classList.add('navbar-toggler-icon-clicked');
    } else {
        icon.classList.remove('navbar-toggler-icon-clicked');
        icon.classList.add('navbar-toggler-icon');
    }
});