var gulp = require('gulp');
var path = require('path');

gulp.task('build', function() {
    // Copiar archivos de swagger-ui
    var swagger_dir = path.join('node_modules', 'swagger-ui-dist');
    var globs = [
        path.join(swagger_dir, '*.html'),
        path.join(swagger_dir, '*.js'),
        path.join(swagger_dir, '*.css')
    ];

    gulp.src(globs).pipe(gulp.dest('.'));

    // Copiar archivos de swagger-ui-themes
    gulp.src(path.join('node_modules', 'swagger-ui-themes', 'themes', '3.x',
                       '*.css')).pipe(gulp.dest('.'))

    // Copiar archivos propios de /src
    gulp.src(path.join('src', '**')).pipe(gulp.dest('.'));
});